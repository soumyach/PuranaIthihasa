"""Immutable, hash-scoped approval records with constrained inheritance."""

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
}
NON_INHERITABLE_SUBJECTS = {"SOURCE_READINESS", "MANUSCRIPT", "PAGE_COMPOSITION", "THEOLOGICAL_RESOLUTION"}


class ApprovalStore:
    def __init__(self, root):
        self.root = Path(root)

    def create(self, approval_type, subject_type, subject_hash, scope, approver, creator, decision,
               inheritance_allowed=False, conditions=None, invalidators=None, evidence_refs=None):
        if approval_type not in APPROVAL_TYPES or decision not in DECISIONS:
            raise ContractError("invalid approval type or decision")
        if not subject_hash or not isinstance(scope, dict) or not scope.get("type") or not scope.get("id"):
            raise ContractError("approval requires a subject hash and typed scope")
        if approver.get("id") == creator.get("id"):
            raise ContractError("an artifact creator cannot independently approve it")
        if inheritance_allowed and subject_type in NON_INHERITABLE_SUBJECTS:
            raise ContractError("%s approvals cannot be inherited" % subject_type)
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
            "created_at": utc_now(),
        }
        record["id"] = stable_id("approval", approval_type, subject_hash, scope["type"], scope["id"], approver["id"], decision)
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

    def find_valid(self, subject_type, subject_hash, target_scope, current_invalidators=None):
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
            if (record["subject_type"], record["subject_hash"], record["scope"]["type"], record["scope"]["id"]) in revoked_scopes:
                continue
            exact = all(record["scope"].get(key) == target_scope.get(key) for key in ("type", "id"))
            inherited = record["inheritance_allowed"] and target_scope.get("ancestors") and record["scope"]["id"] in target_scope["ancestors"]
            if (exact or inherited) and not changed.intersection(record.get("invalidators", [])):
                candidates.append((1 if exact else 0, record))
        candidates.sort(key=lambda item: (item[0], item[1]["created_at"], item[1]["id"]))
        return candidates[-1][1] if candidates else None
