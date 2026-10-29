"""Reconcile later immutable production evidence with the historical run log.

The legacy ``run/events.jsonl`` remains immutable.  Campaigns created by later
production milestones are bound through a small, hash-pinned evidence manifest
and projected into ``orchestration/effective-state.json``.  The projection is
deterministic and repairable; none of the evidence it describes is rewritten.
"""

from collections import Counter
from copy import deepcopy
from pathlib import Path

from .errors import ContractError
from .state import StateStore
from .util import atomic_json_write, content_hash, load_json, sha256_bytes


EVIDENCE_ROLES = {
    "historical_events",
    "historical_state",
    "campaign_request",
    "campaign_status",
    "execution_ledger",
    "completed_pages",
    "campaign_image_reviews",
    "composed_page_reviews",
    "campaign_approval",
    "invalidation_source",
    "brahma_reference_proposal",
    "vishnu_reference_proposal",
}


def _version_number(path):
    stem = Path(path).stem
    marker = stem.rsplit(".v", 1)
    if len(marker) != 2 or not marker[1].isdigit():
        raise ContractError("reconciliation evidence file requires a .vNNNN version", {"path": str(path)})
    return int(marker[1])


class ProductionStateReconciler:
    """Build a current, fail-closed book state from hash-bound evidence."""

    def __init__(self, repository_root, books_root=None):
        self.root = Path(repository_root).resolve()
        self.books_root = Path(books_root).resolve() if books_root else self.root / "books"

    def evidence_paths(self, book_id):
        evidence_root = self.books_root / book_id / "production-reconciliation"
        paths = sorted(evidence_root.glob("evidence.v*.json"), key=_version_number)
        versions = [_version_number(path) for path in paths]
        if len(versions) != len(set(versions)):
            raise ContractError("conflicting reconciliation evidence versions", {"book_id": book_id})
        if versions and versions != list(range(1, versions[-1] + 1)):
            raise ContractError("reconciliation evidence versions are not contiguous", {"book_id": book_id})
        return paths

    def has_evidence(self, book_id):
        return bool(self.evidence_paths(book_id))

    def _safe_path(self, value):
        if not isinstance(value, str) or not value or Path(value).is_absolute():
            raise ContractError("evidence path must be a non-empty repository-relative path")
        path = (self.root / value).resolve()
        try:
            path.relative_to(self.root)
        except ValueError as exc:
            raise ContractError("evidence path escapes the repository", {"path": value}) from exc
        if not path.is_file():
            raise ContractError("reconciliation evidence file is missing", {"path": value})
        return path

    def _load_manifest_chain(self, book_id):
        manifests = []
        previous_sha = None
        for sequence, path in enumerate(self.evidence_paths(book_id), 1):
            manifest = load_json(path)
            if manifest.get("schema_version") != "1.0" or manifest.get("record_type") != "PRODUCTION_RECONCILIATION_EVIDENCE":
                raise ContractError("unsupported reconciliation evidence record", {"path": str(path)})
            if manifest.get("book_id") != book_id or manifest.get("sequence") != sequence:
                raise ContractError("reconciliation evidence identity or sequence mismatch", {"path": str(path)})
            if sequence == 1 and manifest.get("supersedes_sha256") is not None:
                raise ContractError("first reconciliation evidence record cannot supersede another record")
            if sequence > 1 and manifest.get("supersedes_sha256") != previous_sha:
                raise ContractError("reconciliation evidence chain is inconsistent", {"path": str(path)})
            previous_sha = sha256_bytes(path.read_bytes())
            manifests.append((manifest, path, previous_sha))
        return manifests

    def _evidence(self, manifest):
        items = manifest.get("evidence")
        if not isinstance(items, list) or not items:
            raise ContractError("reconciliation manifest requires evidence records")
        by_role = {}
        for item in items:
            role = item.get("role")
            if role not in EVIDENCE_ROLES or role in by_role:
                raise ContractError("unknown or duplicate reconciliation evidence role", {"role": role})
            path = self._safe_path(item.get("path"))
            actual = sha256_bytes(path.read_bytes())
            if item.get("sha256") != actual:
                raise ContractError("reconciliation evidence hash mismatch", {"path": item.get("path")})
            by_role[role] = {"record": item, "path": path, "sha256": actual}
        required = {
            "historical_events", "historical_state", "campaign_request", "campaign_status",
            "execution_ledger", "completed_pages", "campaign_image_reviews",
            "composed_page_reviews", "campaign_approval", "invalidation_source",
        }
        missing = required - set(by_role)
        if missing:
            raise ContractError("reconciliation manifest lacks required evidence", {"missing": sorted(missing)})
        return by_role

    def _verify_campaign(self, book_id, manifest, evidence):
        campaign = manifest.get("campaign", {})
        campaign_id = campaign.get("campaign_id")
        subject_hash = campaign.get("subject_hash")
        if not campaign_id or not subject_hash:
            raise ContractError("reconciliation manifest lacks campaign identity")

        request = load_json(evidence["campaign_request"]["path"])
        status = load_json(evidence["campaign_status"]["path"])
        ledger = load_json(evidence["execution_ledger"]["path"])
        completed = load_json(evidence["completed_pages"]["path"])
        approval = load_json(evidence["campaign_approval"]["path"])
        image_reviews = load_json(evidence["campaign_image_reviews"]["path"])
        page_reviews = load_json(evidence["composed_page_reviews"]["path"])

        for name, record in {
            "request": request, "status": status, "ledger": ledger, "completed": completed,
            "image_reviews": image_reviews, "page_reviews": page_reviews,
        }.items():
            if record.get("book_id") != book_id:
                raise ContractError("campaign evidence belongs to another book", {"record": name})
            record_campaign = record.get("campaign_id")
            if record_campaign is not None and record_campaign != campaign_id:
                raise ContractError("campaign evidence identity conflict", {"record": name})

        if request.get("authorization_subject_hash") != subject_hash:
            raise ContractError("campaign request subject differs from reconciliation manifest")
        if status.get("subject_hash") != subject_hash or ledger.get("authorization_subject_hash") != subject_hash:
            raise ContractError("campaign execution evidence has conflicting authorization subjects")
        if completed.get("authorization_subject_hash") != subject_hash:
            raise ContractError("completed-page evidence has a conflicting authorization subject")
        if approval.get("id") != status.get("approval_id") or approval.get("id") != ledger.get("approval_id"):
            raise ContractError("campaign approval identity conflict")
        if approval.get("subject_hash") != subject_hash or approval.get("decision") not in {"PASS", "PASS_WITH_CONDITIONS"}:
            raise ContractError("campaign approval does not authorize the exact subject")
        if approval.get("scope") != {"type": "book", "id": book_id} or approval.get("inheritance_allowed") is not False:
            raise ContractError("campaign approval scope is not exact and non-inheritable")

        operations = ledger.get("operations")
        counts = ledger.get("operation_counts", {})
        status_counts = status.get("operations", {})
        if not isinstance(operations, list) or counts.get("total") != len(operations):
            raise ContractError("execution ledger operation count mismatch")
        if counts.get("total") != status_counts.get("total_executed"):
            raise ContractError("campaign status and execution ledger disagree on executed operations")
        if counts.get("ceiling") != status_counts.get("total_ceiling") or counts.get("total", 0) > counts.get("ceiling", -1):
            raise ContractError("campaign ceiling conflict")
        if counts.get("necessary") != status_counts.get("necessary_executed"):
            raise ContractError("necessary operation count conflict")
        if counts.get("conditional_derived_fallback") != status_counts.get("conditional_fallback_executed"):
            raise ContractError("derived fallback operation count conflict")
        if counts.get("review_directed_repair") != status_counts.get("review_directed_repairs_executed"):
            raise ContractError("repair operation count conflict")

        subject = request.get("authorization_subject", {})
        allowed_units = {
            item["unit_id"].rsplit("--", 1)[-1]
            for group in ("necessary_operations", "conditional_derived_fallback_operations")
            for item in subject.get(group, [])
        }
        operation_indices = []
        provider_ids = []
        attempts = Counter()
        repair_attempts = Counter()
        operation_classes = Counter()
        output_hashes = []
        for operation in operations:
            index = operation.get("operation_index")
            unit_id = operation.get("unit_id")
            if not isinstance(index, int) or not unit_id or unit_id not in allowed_units:
                raise ContractError("execution ledger contains an operation outside campaign scope", {"unit_id": unit_id})
            operation_indices.append(index)
            attempts[unit_id] += 1
            operation_class = operation.get("operation_class")
            operation_classes[operation_class] += 1
            if operation_class == "REVIEW_DIRECTED_REPAIR":
                repair_attempts[unit_id] += 1
            output_path = self._safe_path(operation.get("output_path"))
            output_hash = sha256_bytes(output_path.read_bytes())
            if output_hash != operation.get("output_sha256"):
                raise ContractError("executed image hash differs from its receipt", {"unit_id": unit_id})
            output_hashes.append(output_hash)
            provider_ids.append(operation.get("provider_operation_identifier"))
        if operation_indices != list(range(1, len(operations) + 1)):
            raise ContractError("execution ledger operation indices are not contiguous")
        if None in provider_ids or len(provider_ids) != len(set(provider_ids)):
            raise ContractError("provider operation identifiers are missing or duplicated")
        if any(value > 2 for value in attempts.values()) or any(value > 1 for value in repair_attempts.values()):
            raise ContractError("per-unit campaign attempt ceiling was exceeded")
        if (
            operation_classes["NECESSARY_NEW_MASTER"]
            + operation_classes["NECESSARY_TARGETED_EDIT"] != counts.get("necessary")
            or operation_classes["CONDITIONAL_DERIVED_PANEL_FALLBACK"] != counts.get("conditional_derived_fallback")
            or operation_classes["REVIEW_DIRECTED_REPAIR"] != counts.get("review_directed_repair")
            or set(operation_classes) - {
                "NECESSARY_NEW_MASTER", "NECESSARY_TARGETED_EDIT",
                "CONDITIONAL_DERIVED_PANEL_FALLBACK", "REVIEW_DIRECTED_REPAIR",
            }
        ):
            raise ContractError("execution ledger operation classes conflict with their counters")
        if ledger.get("provider") != "CODEX_BUILT_IN_IMAGE_GENERATION_ONLY":
            raise ContractError("campaign used an unapproved provider")
        if any(ledger.get(field) is not False for field in (
            "api_key_used", "external_provider_used", "explicit_payment_requested",
            "purchased_credit_use_intended_or_authorized", "automatic_retry",
        )):
            raise ContractError("campaign ledger violates its spending or retry policy")

        page_status = status.get("pages", {})
        complete_numbers = completed.get("complete_page_numbers", [])
        if complete_numbers != page_status.get("complete_page_numbers"):
            raise ContractError("completed-page records disagree")
        if completed.get("complete_private_preview_pages") != len(complete_numbers):
            raise ContractError("completed-page count is inconsistent")
        incomplete = completed.get("incomplete", [])
        incomplete_numbers = [item.get("page_number") for item in incomplete]
        if incomplete_numbers != page_status.get("blocked_page_numbers"):
            raise ContractError("blocked-page records disagree")
        if set(complete_numbers).intersection(incomplete_numbers):
            raise ContractError("a page is both complete and blocked")
        if len(complete_numbers) + len(incomplete_numbers) != page_status.get("total"):
            raise ContractError("page inventory is incomplete")
        accepted_artifacts = []
        for page in completed.get("complete", []):
            path = self._safe_path(page.get("path"))
            actual = sha256_bytes(path.read_bytes())
            if actual != page.get("sha256"):
                raise ContractError("accepted composed-page artifact hash mismatch", {"page": page.get("page_number")})
            composition = load_json(self._safe_path(page.get("composition_path")))
            validation = load_json(self._safe_path(page.get("validation_path")))
            review = load_json(self._safe_path(page.get("independent_review_path")))
            if page.get("deterministic_validation") != "PASS" or page.get("independent_actual_pixel_review") != "PASS":
                raise ContractError("completed page lacks required validation", {"page": page.get("page_number")})
            if composition.get("book_id") != book_id or composition.get("page_id") != page.get("page_id"):
                raise ContractError("completed page composition identity conflict", {"page": page.get("page_number")})
            if validation.get("page_id") != page.get("page_id") or validation.get("result") != "PASS":
                raise ContractError("completed page deterministic validation conflict", {"page": page.get("page_number")})
            reviewer = review.get("reviewer", {})
            if (
                review.get("book_id") not in {None, book_id}
                or review.get("page_id") not in {None, page.get("page_id")}
                or review.get("composed_png", {}).get("sha256") != actual
                or review.get("overall_verdict") != "PASS"
                or review.get("private_pdf_proof_eligible") is not True
                or review.get("publication_eligible") is not False
                or reviewer.get("independent_of_composer") is not True
                or reviewer.get("actual_pixels_inspected") is not True
            ):
                raise ContractError("completed page independent review conflict", {"page": page.get("page_number")})
            accepted_artifacts.append({
                "page_number": page["page_number"], "page_id": page["page_id"],
                "path": page["path"], "sha256": actual,
            })
        if len(accepted_artifacts) != len(complete_numbers):
            raise ContractError("completed-page artifact inventory is incomplete")

        return {
            "request": request,
            "status": status,
            "ledger": ledger,
            "completed": completed,
            "approval": approval,
            "image_reviews": image_reviews,
            "page_reviews": page_reviews,
            "attempts": dict(sorted(attempts.items())),
            "repair_attempts": dict(sorted(repair_attempts.items())),
            "output_hashes": output_hashes,
            "accepted_artifacts": accepted_artifacts,
            "allowed_units": sorted(allowed_units),
        }

    def _historical_state(self, book_id, evidence):
        events_path = evidence["historical_events"]["path"]
        state_path = evidence["historical_state"]["path"]
        expected_events = self.books_root / book_id / "run" / "events.jsonl"
        expected_state = self.books_root / book_id / "run" / "state.json"
        if events_path != expected_events.resolve() or state_path != expected_state.resolve():
            raise ContractError("historical state evidence does not bind the canonical run paths")
        state = StateStore(self.books_root, book_id).replay()
        if state != load_json(state_path):
            raise ContractError("historical state materialization conflicts with its event replay")
        return state

    def reconcile(self, book_id, persist=False):
        chain = self._load_manifest_chain(book_id)
        if not chain:
            return None
        manifest, manifest_path, manifest_sha = chain[-1]
        evidence = self._evidence(manifest)
        historical = self._historical_state(book_id, evidence)
        campaign = self._verify_campaign(book_id, manifest, evidence)

        invalidations = manifest.get("invalidations", [])
        active_invalidations = [item for item in invalidations if item.get("status") == "ACTIVE"]
        invalidated_pages = sorted({page for item in active_invalidations for page in item.get("page_numbers", [])})
        invalidated_units = sorted({unit for item in active_invalidations for unit in item.get("unit_ids", [])})
        additional_candidates = manifest.get("additional_resume_candidate_unit_ids", [])
        if (
            not isinstance(additional_candidates, list)
            or any(not isinstance(unit, str) or not unit for unit in additional_candidates)
        ):
            raise ContractError("additional resume candidates must be a list of non-empty unit IDs")
        separately_gated_units = sorted({
            unit
            for item in active_invalidations
            for unit in item.get("qualified_review_then_regeneration", [])
        })
        if set(additional_candidates).intersection(separately_gated_units):
            raise ContractError("a separately gated unit cannot be added to ordinary resume candidates")
        recorded_complete = campaign["completed"]["complete_page_numbers"]
        effective_complete = sorted(set(recorded_complete) - set(invalidated_pages))
        original_recovery = {
            item["page_number"]: [item["reason"]]
            for item in campaign["completed"].get("incomplete", [])
        }
        for item in active_invalidations:
            reason = item.get("reason")
            if not reason:
                raise ContractError("active invalidation requires a reason")
            for page in item.get("page_numbers", []):
                original_recovery.setdefault(page, []).append(reason)
        blocked_pages = sorted(set(range(1, campaign["status"]["pages"]["total"] + 1)) - set(effective_complete))
        if set(original_recovery) != set(blocked_pages):
            missing = sorted(set(blocked_pages) - set(original_recovery))
            raise ContractError("effective blocked pages lack recovery requirements", {"pages": missing})

        preserved_gates = {
            key: value
            for key, value in campaign["status"].items()
            if isinstance(value, dict) and value.get("status") == "ESCALATE_BEFORE_GENERATION"
        }
        for key, gate in preserved_gates.items():
            if gate.get("generated") is not False or gate.get("qualified_review_signed") is not False:
                raise ContractError("qualified pre-generation gate conflicts with locked evidence", {"gate": key})
        if separately_gated_units and not preserved_gates:
            raise ContractError("separately gated units lack a preserved pre-generation gate")

        counts = campaign["ledger"]["operation_counts"]
        blockers = deepcopy(manifest.get("effective_blockers", []))
        blocker_codes = [item.get("code") for item in blockers]
        if (
            not blockers
            or len(blocker_codes) != len(set(blocker_codes))
            or any(not item.get("code") or not item.get("owner") or not item.get("detail") for item in blockers)
        ):
            raise ContractError("effective reconciliation blockers are incomplete or conflicting")

        effective = {
            "schema_version": "1.0",
            "book_id": book_id,
            "fixture_mode": False,
            "publication_eligible": False,
            "current_stage": "ILLUSTRATION",
            "effective_status": "BLOCKED",
            "completed_stages": [
                "SOURCE_CHECK", "MANUSCRIPT", "EDITORIAL_QA", "STORYBOARD",
                "CHARACTER_BIBLE", "ART_PROOFS", "AWAITING_STYLE_APPROVAL",
            ],
            "dimensions": {
                "source_readiness": "BLOCKED_CONTROLLED_PRIVATE_SCOPE_ONLY",
                "private_production_clearance": "PRIOR_CAMPAIGN_SCOPE_CLOSED",
                "editorial_certification": "PASS_DUAL_PERSPECTIVE_PRIVATE_SCOPE",
                "visual_completion": "PARTIAL_WITH_ACTIVE_INVALIDATIONS",
                "publication_clearance": "BLOCKED",
                "publication_artifact_readiness": "NOT_READY",
            },
            "blocked": blockers,
            "campaign": {
                "campaign_id": campaign["ledger"]["campaign_id"],
                "subject_hash": campaign["ledger"]["authorization_subject_hash"],
                "approval_id": campaign["approval"]["id"],
                "scope_closed": True,
                "total_executed": counts["total"],
                "total_ceiling": counts["ceiling"],
                "unspent_conditional_reserve": counts.get("unspent_conditional_reserve", 0),
                "operations_authorized_for_resume": 0,
                "attempts_by_unit": campaign["attempts"],
                "repair_attempts_by_unit": campaign["repair_attempts"],
                "allowed_unit_ids": campaign["allowed_units"],
                "executed_output_hashes": campaign["output_hashes"],
            },
            "pages": {
                "total": campaign["status"]["pages"]["total"],
                "recorded_complete_before_invalidation": recorded_complete,
                "effective_complete": effective_complete,
                "blocked": blocked_pages,
                "invalidated_after_campaign": invalidated_pages,
                "recovery_requirements": [
                    {"page_number": page, "requirements": original_recovery[page]}
                    for page in blocked_pages
                ],
                "accepted_artifacts_preserved": campaign["accepted_artifacts"],
            },
            **preserved_gates,
            "active_invalidations": active_invalidations,
            "invalidated_unit_ids": invalidated_units,
            "resume_policy": {
                "prior_campaign_reusable": False,
                "new_campaign_required": True,
                "currently_eligible_unit_ids": [],
                "candidate_unit_ids_after_required_approvals": sorted(
                    (set(invalidated_units) | set(additional_candidates)) - set(separately_gated_units)
                ),
                "separately_gated_unit_ids": separately_gated_units,
                "duplicate_generation_prohibited": True,
            },
            "historical_state": {
                "current_stage": historical["current_stage"],
                "version": historical["version"],
                "last_event_id": historical["last_event_id"],
                "preserved": True,
            },
            "reconciliation": {
                "effective": True,
                "manifest_path": manifest_path.relative_to(self.root).as_posix(),
                "manifest_sha256": manifest_sha,
                "evidence_sha256": {
                    role: item["sha256"] for role, item in sorted(evidence.items())
                },
                "conflicts_detected": False,
                "historical_state_overwritten": False,
            },
        }
        effective["effective_state_hash"] = content_hash(effective)
        if persist:
            destination = self.books_root / book_id / "orchestration" / "effective-state.json"
            if not destination.is_file() or load_json(destination) != effective:
                atomic_json_write(destination, effective)
        return effective
