"""Immutable, hash-scoped approval records with constrained inheritance."""

from datetime import datetime, timezone
from pathlib import Path

from .errors import ContractError
from .util import atomic_json_write, load_json, stable_id, utc_now


DECISIONS = {"PASS", "PASS_WITH_CONDITIONS", "FAIL", "REVOKED"}
APPROVAL_TYPES = {
    "VISUAL_STYLE_OR_CHARACTER_FAMILY",
    "SOURCE_OR_THEOLOGICAL_UNCERTAINTY",
    "ICONOGRAPHY_DEVIATION",
    "BUDGET_OVERRUN",
    "REPEATED_QA_FAILURE",
    "SERIES_VISUAL_STANDARD",
    "COLLECTION_STYLE",
    "CHARACTER_FAMILY",
    "BOOK_THEOLOGICAL_EXCEPTION",
    "MANUSCRIPT_SOURCE_DISPUTE",
}
NON_INHERITABLE_SUBJECTS = {"SOURCE_READINESS", "MANUSCRIPT", "PAGE_COMPOSITION", "THEOLOGICAL_RESOLUTION"}
NON_INHERITABLE_APPROVAL_TYPES = {"BOOK_THEOLOGICAL_EXCEPTION", "MANUSCRIPT_SOURCE_DISPUTE"}
APPROVAL_SCOPE_TYPES = {
    "SERIES_VISUAL_STANDARD": "series",
    "COLLECTION_STYLE": "collection",
    "CHARACTER_FAMILY": "character_family",
    "BOOK_THEOLOGICAL_EXCEPTION": "book",
    "MANUSCRIPT_SOURCE_DISPUTE": "manuscript",
}


class ApprovalStore:
    def __init__(self, root):
        self.root = Path(root)

    def create(self, approval_type, subject_type, subject_hash, scope, approver, creator, decision,
               inheritance_allowed=False, conditions=None, invalidators=None, evidence_refs=None,
               source_scope=None, tradition_id=None, edition_id=None, evidence_hash=None,
               expires_at=None):
        if approval_type not in APPROVAL_TYPES or decision not in DECISIONS:
            raise ContractError("invalid approval type or decision")
        if not subject_hash or not isinstance(scope, dict) or not scope.get("type") or not scope.get("id"):
            raise ContractError("approval requires a subject hash and typed scope")
        expected_scope = APPROVAL_SCOPE_TYPES.get(approval_type)
        if expected_scope and scope["type"] != expected_scope:
            raise ContractError("%s approvals require %s scope" % (approval_type, expected_scope))
        if approver.get("id") == creator.get("id"):
            raise ContractError("an artifact creator cannot independently approve it")
        if inheritance_allowed and subject_type in NON_INHERITABLE_SUBJECTS:
            raise ContractError("%s approvals cannot be inherited" % subject_type)
        if inheritance_allowed and approval_type in NON_INHERITABLE_APPROVAL_TYPES:
            raise ContractError("%s approvals cannot be inherited" % approval_type)
        record = {
            "schema_version": "1.0",
            "approval_type": approval_type,
            "subject_type": subject_type,
            "subject_hash": subject_hash,
            "scope": scope,
            "approver": approver,
            "creator": creator,
            "decision": decision,
            "inheritance_allowed": bool(inheritance_allowed),
            "conditions": conditions or [],
            "invalidators": sorted(invalidators or []),
            "evidence_refs": sorted(evidence_refs or []),
            "source_scope": source_scope,
            "tradition_id": tradition_id,
            "edition_id": edition_id,
            "evidence_hash": evidence_hash or subject_hash,
            "expires_at": expires_at,
            "created_at": utc_now(),
        }
        record["id"] = stable_id(
            "approval", approval_type, subject_hash, scope["type"], scope["id"],
            source_scope, tradition_id, edition_id, record["evidence_hash"], expires_at,
            approver["id"], decision,
        )
        path = self.root / (record["id"] + ".json")
        if path.exists():
            existing = load_json(path)
            comparable_existing = dict(existing)
            comparable_record = dict(record)
            comparable_existing.pop("created_at", None)
            comparable_record.pop("created_at", None)
            if comparable_existing != comparable_record:
                raise ContractError("approval id already exists with different content")
            return existing
        atomic_json_write(path, record)
        return record

    def list(self):
        return [load_json(path) for path in sorted(self.root.glob("*.json"))]

    @staticmethod
    def _expired(record):
        value = record.get("expires_at")
        if not value:
            return False
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return True
        return parsed <= datetime.now(timezone.utc)

    @staticmethod
    def _same_source_boundary(record, target_context):
        context = target_context or {}
        for field in ("source_scope", "tradition_id", "edition_id"):
            approved = record.get(field)
            target = context.get(field)
            if approved != target:
                return False
        return True

    def find_valid(self, subject_type, subject_hash, target_scope, current_invalidators=None,
                   target_context=None, current_evidence_hash=None):
        changed = set(current_invalidators or [])
        candidates = []
        records = self.list()
        revoked_scopes = {
            (record["subject_type"], record["subject_hash"], record["scope"]["type"], record["scope"]["id"])
            for record in records if record["decision"] == "REVOKED"
        }
        for record in records:
            if record["subject_type"] != subject_type or record["subject_hash"] != subject_hash:
                continue
            if record["decision"] not in {"PASS", "PASS_WITH_CONDITIONS"}:
                continue
            if self._expired(record):
                continue
            if current_evidence_hash and record.get("evidence_hash") != current_evidence_hash:
                continue
            if (record["subject_type"], record["subject_hash"], record["scope"]["type"], record["scope"]["id"]) in revoked_scopes:
                continue
            exact = all(record["scope"].get(key) == target_scope.get(key) for key in ("type", "id"))
            inherited = (
                record["inheritance_allowed"]
                and target_scope.get("ancestors")
                and record["scope"]["id"] in target_scope["ancestors"]
                and self._same_source_boundary(record, target_context)
            )
            if (exact or inherited) and not changed.intersection(record.get("invalidators", [])):
                candidates.append((1 if exact else 0, record))
        candidates.sort(key=lambda item: (item[0], item[1]["created_at"], item[1]["id"]))
        return candidates[-1][1] if candidates else None
