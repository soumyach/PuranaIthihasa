"""Durable, fail-closed orchestration for the complete Book Factory lifecycle.

Repository code can validate, render, persist and route work.  It cannot spawn
Codex specialists, impersonate a human approver, or manufacture provider
results.  This module makes those boundaries first-class job outcomes while an
explicit fixture plan can exercise the same state machine in isolated tests.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from .approvals import ApprovalStore
from .artifacts import ArtifactStore
from .budgets import BudgetGuard
from .errors import BudgetExceededError, ContractError
from .locks import BookLease
from .page_engine import compose_book, export_pdf, inspect_pdf
from .rules import rules_status
from .source_clearance import validate_private_draft_clearance
from .state import STAGES, StateStore, job_key
from .util import append_jsonl, atomic_json_write, content_hash, load_json, stable_id, utc_now


ORCHESTRATED_STAGES = STAGES[1:]
RESULTS = {"PASS", "FIX", "ESCALATE"}
EXECUTION_KINDS = {
    "SOURCE_CHECK": "REPOSITORY_EXECUTABLE",
    "MANUSCRIPT": "ACTIVE_CODEX_ORCHESTRATION",
    "EDITORIAL_QA": "ACTIVE_CODEX_ORCHESTRATION_INDEPENDENT",
    "STORYBOARD": "ACTIVE_CODEX_ORCHESTRATION",
    "CHARACTER_BIBLE": "ACTIVE_CODEX_ORCHESTRATION",
    "ART_PROOFS": "EXTERNAL_IMAGE_PROVIDER",
    "AWAITING_STYLE_APPROVAL": "HUMAN_AUTHORIZATION",
    "ILLUSTRATION": "EXTERNAL_IMAGE_PROVIDER",
    "LETTERING": "REPOSITORY_EXECUTABLE",
    "PDF_LAYOUT": "REPOSITORY_EXECUTABLE",
    "VISUAL_QA": "ACTIVE_CODEX_ORCHESTRATION_INDEPENDENT_IMAGE_REVIEW",
    "READY_FOR_PUBLICATION": "REPOSITORY_GATE",
}
WORKERS = {
    "SOURCE_CHECK": "source-evidence",
    "MANUSCRIPT": "manuscript-story",
    "EDITORIAL_QA": "independent-editorial-review-gate",
    "STORYBOARD": "art-iconography",
    "CHARACTER_BIBLE": "art-iconography",
    "ART_PROOFS": "illustration-producer",
    "AWAITING_STYLE_APPROVAL": "human-style-approver",
    "ILLUSTRATION": "illustration-producer",
    "LETTERING": "typesetter-page-composer",
    "PDF_LAYOUT": "page-composition-engine",
    "VISUAL_QA": "independent-image-capable-reviewer",
    "READY_FOR_PUBLICATION": "publication-readiness-gate",
}
SPECIALIST_ROLES = {
    "SOURCE_CHECK": ["source-evidence-specialist"],
    "MANUSCRIPT": ["manuscript-story-specialist"],
    "EDITORIAL_QA": ["family-reader-editor", "independent-theological-source-reviewer"],
    "STORYBOARD": ["art-iconography-specialist"],
    "CHARACTER_BIBLE": ["art-iconography-specialist"],
    "ART_PROOFS": ["illustration-producer"],
    "AWAITING_STYLE_APPROVAL": ["authorized-human-approver"],
    "ILLUSTRATION": ["illustration-producer"],
    "LETTERING": ["typesetter-page-composer"],
    "PDF_LAYOUT": ["typesetter-page-composer"],
    "VISUAL_QA": ["independent-image-capable-reviewer"],
    "READY_FOR_PUBLICATION": ["publication-readiness-gate"],
}
INDEPENDENT_STAGES = {"EDITORIAL_QA", "VISUAL_QA"}
PROVIDER_STAGES = {"ART_PROOFS", "ILLUSTRATION"}
CODEX_STAGES = {"MANUSCRIPT", "EDITORIAL_QA", "STORYBOARD", "CHARACTER_BIBLE", "VISUAL_QA"}
HUMAN_STAGES = {"AWAITING_STYLE_APPROVAL"}


def _stage_index(stage):
    if stage not in STAGES:
        raise ContractError("unknown orchestration stage", {"stage": stage})
    return STAGES.index(stage)


def _normalized_hashes(values):
    result = sorted(set(values or []))
    if any(not isinstance(value, str) or not value for value in result):
        raise ContractError("hash bindings must be non-empty strings")
    return result


class JobLedger:
    """Append-only job events plus repairable current-job materializations."""

    def __init__(self, books_root, book_id, fixture_mode=False):
        self.book_id = book_id
        self.fixture_mode = bool(fixture_mode)
        self.root = Path(books_root) / book_id / "orchestration"
        self.jobs_root = self.root / "jobs"
        self.events_path = self.root / "events.jsonl"

    def events(self):
        if not self.events_path.is_file():
            return []
        records = []
        with self.events_path.open("r", encoding="utf-8") as handle:
            for number, line in enumerate(handle, 1):
                if line.strip():
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise ContractError("invalid orchestration event", {"line": number}) from exc
                    if record.get("sequence") != len(records) + 1:
                        raise ContractError("orchestration event sequence is not contiguous")
                    records.append(record)
        return records

    def _path(self, job_id):
        return self.jobs_root / (job_id + ".json")

    def jobs(self):
        return [load_json(path) for path in sorted(self.jobs_root.glob("*.json"))]

    def _write(self, record, event_type):
        record = deepcopy(record)
        record["record_hash"] = content_hash({key: value for key, value in record.items() if key != "record_hash"})
        atomic_json_write(self._path(record["job_id"]), record)
        events = self.events()
        append_jsonl(self.events_path, {
            "schema_version": "1.0",
            "sequence": len(events) + 1,
            "event_id": stable_id("orchestration-event", self.book_id, len(events) + 1, event_type, record["record_hash"]),
            "event_type": event_type,
            "book_id": self.book_id,
            "job_id": record["job_id"],
            "stage": record["stage"],
            "status": record["status"],
            "record_hash": record["record_hash"],
            "timestamp": utc_now(),
            "job_snapshot": record,
        })
        return record

    def current(self, stage):
        candidates = [job for job in self.jobs() if job["stage"] == stage]
        candidates.sort(key=lambda item: (item["attempt_number"], item["job_id"]))
        return candidates[-1] if candidates else None

    def invalidate_from(self, stage, reason, changed_input_hashes=None, page_id=None):
        invalidated = []
        boundary = _stage_index(stage)
        for record in self.jobs():
            if record["status"] == "INVALIDATED" or _stage_index(record["stage"]) < boundary:
                continue
            if page_id and record.get("page_id") not in {None, page_id}:
                continue
            record["status"] = "INVALIDATED"
            record["result"] = "ESCALATE"
            record["completed_at"] = utc_now()
            record["recovery_instructions"] = {
                "action": "REEXECUTE_WITH_CHANGED_INPUTS",
                "reason": reason,
                "changed_input_hashes": _normalized_hashes(changed_input_hashes),
                "scope": "PAGE_LOCAL" if page_id else "DEPENDENT_STAGES_ONLY",
                "page_id": page_id,
            }
            self._write(record, "JOB_INVALIDATED")
            invalidated.append(record["job_id"])
        return invalidated

    def begin(self, stage, input_hashes, policy_hashes, worker_identity, provider_config_hash="none",
              page_id=None, estimated_cost_minor_units=0, max_attempts=None):
        if stage not in ORCHESTRATED_STAGES:
            raise ContractError("stage cannot be executed as an orchestration job", {"stage": stage})
        inputs = _normalized_hashes(input_hashes)
        policies = _normalized_hashes(policy_hashes)
        identifier = job_key(
            self.book_id, stage, page_id, inputs, policies,
            worker_identity.get("version", "1.0"), provider_config_hash,
        )
        job_id = stable_id("orchestration-job", self.book_id, stage, page_id, identifier)
        path = self._path(job_id)
        if path.is_file():
            existing = load_json(path)
            if existing["status"] == "COMPLETED" and existing["result"] == "PASS":
                return existing, True
            if existing["status"] in {"RUNNING", "INTERRUPTED"}:
                existing["status"] = "RUNNING"
                existing["resumed_at"] = utc_now()
                existing["recovery_instructions"] = None
                return self._write(existing, "JOB_RESUMED"), False
        prior = self.current(stage)
        if prior and prior["job_id"] != job_id and prior["status"] != "INVALIDATED":
            self.invalidate_from(stage, "stage input fingerprint changed", inputs, page_id=page_id)
        attempts = [job["attempt_number"] for job in self.jobs() if job["stage"] == stage and job.get("page_id") == page_id]
        attempt = max(attempts or [0]) + 1
        if max_attempts is not None and attempt > max_attempts:
            raise BudgetExceededError("stage attempt budget is exhausted", {
                "book_id": self.book_id, "stage": stage, "page_id": page_id,
                "attempt": attempt, "max_attempts": max_attempts,
            })
        started = utc_now()
        record = {
            "schema_version": "1.0",
            "job_id": job_id,
            "book_id": self.book_id,
            "stage": stage,
            "page_id": page_id,
            "status": "RUNNING",
            "result": None,
            "fixture_mode": self.fixture_mode,
            "publication_eligible": False,
            "input_hashes": inputs,
            "output_hashes": [],
            "policy_hashes": policies,
            "worker_identity": deepcopy(worker_identity),
            "execution_receipt": None,
            "attempt_number": attempt,
            "cost": {
                "currency": "USD",
                "estimated_minor_units": estimated_cost_minor_units,
                "actual_minor_units": None,
                "paid_call_executed": False,
            },
            "started_at": started,
            "completed_at": None,
            "recovery_instructions": None,
        }
        return self._write(record, "JOB_STARTED"), False

    def finish(self, record, result, output_hashes, receipt, actual_cost_minor_units=0,
               recovery_instructions=None):
        if result not in RESULTS:
            raise ContractError("job result must be PASS, FIX or ESCALATE")
        if record.get("status") != "RUNNING":
            raise ContractError("only a running job can be completed")
        if not isinstance(receipt, dict) or not receipt.get("mechanism") or not receipt.get("executed_by"):
            raise ContractError("job completion requires an execution receipt")
        if actual_cost_minor_units < 0:
            raise ContractError("actual cost cannot be negative")
        record = deepcopy(record)
        record["status"] = "COMPLETED" if result == "PASS" else "BLOCKED"
        record["result"] = result
        record["output_hashes"] = _normalized_hashes(output_hashes)
        record["execution_receipt"] = deepcopy(receipt)
        record["cost"]["actual_minor_units"] = actual_cost_minor_units
        record["cost"]["paid_call_executed"] = actual_cost_minor_units > 0
        record["completed_at"] = utc_now()
        record["recovery_instructions"] = deepcopy(recovery_instructions)
        if result != "PASS" and not record["recovery_instructions"]:
            raise ContractError("FIX and ESCALATE jobs require recovery instructions")
        return self._write(record, "JOB_COMPLETED" if result == "PASS" else "JOB_BLOCKED")

    def interrupt(self, record, reason="synthetic interruption"):
        record = deepcopy(record)
        record["status"] = "INTERRUPTED"
        record["result"] = "ESCALATE"
        record["completed_at"] = utc_now()
        record["recovery_instructions"] = {
            "action": "RESUME_SAME_JOB_ID",
            "reason": reason,
            "increment_attempt": False,
        }
        return self._write(record, "JOB_INTERRUPTED")


def route_page_repair(finding):
    """Return the smallest safe repair scope for one composed-page finding."""

    code = finding.get("code")
    page_id = finding.get("page_id")
    if not page_id:
        raise ContractError("page-local repair requires a page_id")
    routes = {
        "WRONG_BALLOON_PLACEMENT": ("LETTERING_REPAIR", "LETTERING"),
        "TEXT_OVERFLOW": ("LETTERING_REPAIR", "LETTERING"),
        "INCORRECT_CROP": ("CROP_ADJUSTMENT", "LETTERING"),
        "INCORRECT_ARTWORK": ("LOCAL_IMAGE_EDIT_OR_REGENERATION", "ILLUSTRATION"),
        "WRONG_CHARACTER_APPEARANCE": ("LOCAL_IMAGE_EDIT_OR_REGENERATION", "ILLUSTRATION"),
        "INCORRECT_ICONOGRAPHY": ("LOCAL_IMAGE_EDIT_OR_REGENERATION", "ILLUSTRATION"),
        "CULTURAL_AUTHENTICITY_FAILURE": ("LOCAL_IMAGE_EDIT_OR_REGENERATION", "ILLUSTRATION"),
        "MISSING_PANEL": ("PANEL_REGENERATION", "ILLUSTRATION"),
        "FAILED_PDF_PAGE": ("PAGE_PDF_REEXPORT", "PDF_LAYOUT"),
        "INTERRUPTED_GENERATION": ("RESUME_SAME_JOB_ID", "ILLUSTRATION"),
        "EXPIRED_OR_INVALID_APPROVAL": ("REAPPROVAL", "AWAITING_STYLE_APPROVAL"),
    }
    if code not in routes:
        return {
            "result": "ESCALATE", "page_id": page_id, "panel_id": finding.get("panel_id"),
            "repair_type": "HUMAN_TRIAGE", "restart_stage": "VISUAL_QA",
            "invalidate_scope": "PAGE_LOCAL_PENDING_TRIAGE", "preserve_other_pages": True,
        }
    repair_type, restart = routes[code]
    return {
        "result": "FIX", "page_id": page_id, "panel_id": finding.get("panel_id"),
        "repair_type": repair_type, "restart_stage": restart,
        "invalidate_scope": "PAGE_LOCAL", "preserve_other_pages": True,
        "preserve_prior_versions": True, "reset_retry_counter": False,
    }


def validate_reference_receipt(request, receipt):
    """Prove which A/B/C/D images were actually sent to an image backend."""

    required_roles = {
        "REFERENCE_A_SERIES_VISUAL_IDENTITY",
        "REFERENCE_B_PAGE_COMPOSITION",
        "REFERENCE_C_CHARACTER_IDENTITY",
        "REFERENCE_D_SETTING_ENVIRONMENT",
    }
    references = request.get("references", [])
    declared_roles = [item.get("role") for item in references]
    if set(declared_roles) != required_roles or len(declared_roles) != len(required_roles):
        raise ContractError("reference request must resolve each A/B/C/D role exactly once")
    required_available = {
        item["role"] for item in references
        if item.get("available") and item["role"] in {
            "REFERENCE_A_SERIES_VISUAL_IDENTITY", "REFERENCE_B_PAGE_COMPOSITION"
        }
    }
    if required_available != {
        "REFERENCE_A_SERIES_VISUAL_IDENTITY", "REFERENCE_B_PAGE_COMPOSITION"
    }:
        raise ContractError("series identity and page composition references must be available")
    expected = sorted(
        (item["role"], item["sha256"], item["path"])
        for item in references if item.get("available")
    )
    actual = sorted(
        (item.get("role"), item.get("sha256"), item.get("path"))
        for item in receipt.get("submitted_references", [])
    )
    supports = receipt.get("provider_capabilities", {}).get("reference_images") is True
    if not supports:
        if actual:
            raise ContractError("provider receipt contradicts its reference capability")
        return {
            "result": "ESCALATE",
            "code": "REFERENCE_CONDITIONING_UNSUPPORTED",
            "reference_conditioned": False,
        }
    if actual != expected:
        raise ContractError("provider receipt does not bind the exact requested references")
    return {
        "result": "PASS",
        "reference_conditioned": True,
        "submitted_reference_hashes": [item[1] for item in actual],
        "receipt_hash": content_hash(receipt),
    }


def validate_composed_page_review(request, response):
    """Validate independent actual-pixel page review without judging pixels here."""

    if response.get("rendered_page_hash") != request.get("rendered_page_hash"):
        raise ContractError("visual review does not bind the rendered page hash")
    reviewer = response.get("reviewer", {})
    if not reviewer.get("image_capable") or not reviewer.get("inspected_actual_pixels"):
        return {"result": "ESCALATE", "code": "IMAGE_CAPABLE_REVIEW_NOT_EXECUTED"}
    if reviewer.get("reading_size") != "ACTUAL_READING_SIZE":
        return {"result": "ESCALATE", "code": "ACTUAL_READING_SIZE_NOT_INSPECTED"}
    if reviewer.get("id") in set(request.get("creator_ids", [])):
        return {"result": "ESCALATE", "code": "REVIEWER_INDEPENDENCE_NOT_ESTABLISHED"}
    assessments = response.get("assessments", {})
    required = {"mechanical", "semantic", "artistic_comparison"}
    if set(assessments) != required or any(not assessments[name] for name in required):
        return {"result": "ESCALATE", "code": "REVIEW_DIMENSIONS_INCOMPLETE"}
    values = [item.get("result") for group in assessments.values() for item in group]
    if any(value not in RESULTS for value in values):
        raise ContractError("visual assessment result is invalid")
    result = "ESCALATE" if "ESCALATE" in values else "FIX" if "FIX" in values else "PASS"
    findings = response.get("findings", [])
    if result != "PASS":
        for finding in findings:
            required_finding = {"book_id", "page_id", "panel_id", "discrepancy", "supporting_reference", "severity", "repair_type"}
            if required_finding - set(finding):
                raise ContractError("visual finding lacks targeted repair evidence")
        if not findings:
            raise ContractError("a non-PASS visual review requires findings")
    return {
        "result": result,
        "review_hash": content_hash(response),
        "reviewed_page_hash": request["rendered_page_hash"],
        "image_capable_actual_pixel_review": True,
        "gold_standard_hashes": sorted(request.get("gold_standard_hashes", [])),
        "findings": findings,
    }


class ProductionQueue:
    """Deterministic queue policy with explicit selection and skip evidence."""

    def __init__(self, catalogue, books_root, fixture_mode=False):
        self.catalogue = catalogue
        self.books_root = Path(books_root)
        self.fixture_mode = bool(fixture_mode)

    def _run(self, book_id):
        path = self.books_root / book_id / "orchestration" / "run.json"
        return load_json(path) if path.is_file() else None

    def _legacy_state(self, book_id):
        path = self.books_root / book_id / "run" / "events.jsonl"
        if not path.is_file():
            return None
        return StateStore(self.books_root, book_id).load()

    def _production_status(self, book_id):
        path = self.books_root / book_id / "production-status.json"
        return load_json(path) if path.is_file() else None

    def _production_integration_status(self, book_id):
        path = self.books_root / book_id / "production-integration-status.json"
        return load_json(path) if path.is_file() else None

    def evaluate(self):
        books = self.catalogue.list_books()
        completed = {
            book["id"] for book in books
            if (self._run(book["id"]) or {}).get("current_stage") == "READY_FOR_PUBLICATION"
        }
        rows = []
        for book in books:
            book_id = book["id"]
            run = self._run(book_id)
            state = self._legacy_state(book_id)
            status = self._production_status(book_id)
            integration_status = self._production_integration_status(book_id)
            dependencies = sorted(book.get("dependencies", []))
            missing_dependencies = [item for item in dependencies if item not in completed]
            collection_style_hash = book.get("required_collection_style_hash")
            collection_style_approval = None
            if collection_style_hash and book.get("collection_ids"):
                approval_store = ApprovalStore(self.books_root / "_approvals")
                collection_style_approval = approval_store.find_valid(
                    "COLLECTION_VISUAL_STYLE", collection_style_hash,
                    {"type": "book", "id": book_id, "ancestors": book["collection_ids"]},
                    current_invalidators=book.get("approval_invalidators", []),
                    target_context={
                        "source_scope": book.get("source_scope"),
                        "tradition_id": book.get("tradition_id"),
                        "edition_id": book.get("edition_id"),
                    },
                    current_evidence_hash=book.get("collection_style_evidence_hash", collection_style_hash),
                )
            reasons = []
            queue_status = "ELIGIBLE_NEW"
            if book_id == "DM08" or book.get("edition_status") == "EXISTING_EDITION" or not book.get("automatic_production_eligible", True):
                queue_status = "EXCLUDED"
                reasons.append("EXISTING_EDITION_OR_AUTOMATIC_PRODUCTION_EXCLUDED")
            elif missing_dependencies:
                queue_status = "BLOCKED"
                reasons.append("DEPENDENCIES_NOT_READY")
            elif collection_style_hash and not collection_style_approval:
                queue_status = "BLOCKED"
                reasons.append("COLLECTION_STYLE_APPROVAL_MISSING_OR_INVALID")
            elif run and run.get("current_stage") == "READY_FOR_PUBLICATION":
                queue_status = "COMPLETE"
                reasons.append("PUBLICATION_ARTIFACT_READY_NOT_PUBLISHED")
            elif run and run.get("blocked"):
                queue_status = "BLOCKED"
                reasons.extend(item["code"] for item in run["blocked"])
            elif state and state["current_stage"] not in {"QUEUED", "BLOCKED", "FAILED", "READY_FOR_PUBLICATION"}:
                if status and "RETRY_EXHAUSTED" in status.get("exact_result", ""):
                    queue_status = "BLOCKED"
                    reasons.extend(["ATTEMPT_BUDGET_EXHAUSTED", "STYLE_APPROVAL_UNAVAILABLE"])
                    if integration_status:
                        reasons.extend(item["code"] for item in integration_status.get("blockers", []))
                else:
                    queue_status = "ELIGIBLE_RESUME"
                    reasons.append("PARTIAL_RUN_HAS_DURABLE_STATE")
            elif book.get("readiness") != "READY" and not (self.fixture_mode and book.get("fixture_private_production_eligible")):
                queue_status = "BLOCKED"
                reasons.append("CATALOGUE_NOT_PRIVATE_PRODUCTION_READY")
            elif book.get("private_production_eligible") is False:
                queue_status = "BLOCKED"
                reasons.append("PRIVATE_PRODUCTION_CLEARANCE_BLOCKED")
            else:
                reasons.append("ELIGIBLE_BY_QUEUE_POLICY")
            rows.append({
                "book_id": book_id,
                "title": book.get("title"),
                "priority": book.get("priority", 1000),
                "collection_ids": book.get("collection_ids", []),
                "queue_status": queue_status,
                "reasons": sorted(set(reasons)),
                "dependencies": dependencies,
                "missing_dependencies": missing_dependencies,
                "collection_style_approval_id": collection_style_approval.get("id") if collection_style_approval else None,
                "current_stage": (run or state or {}).get("current_stage", "NOT_STARTED"),
                "source_readiness": (
                    (run or {}).get("dimensions", {}).get("source_readiness")
                    or (status or {}).get("source_readiness")
                    or book.get("readiness")
                ),
                "private_production_eligible": queue_status in {"ELIGIBLE_NEW", "ELIGIBLE_RESUME"},
                "public_publication_eligible": bool(
                    run and run.get("dimensions", {}).get("publication_clearance") == "PASS"
                    and run.get("current_stage") == "READY_FOR_PUBLICATION"
                ),
            })
        selected = sorted(
            (row for row in rows if row["queue_status"] in {"ELIGIBLE_RESUME", "ELIGIBLE_NEW"}),
            key=lambda item: (0 if item["queue_status"] == "ELIGIBLE_RESUME" else 1, item["priority"], item["book_id"]),
        )
        selected_id = selected[0]["book_id"] if selected else None
        for row in rows:
            row["selected"] = row["book_id"] == selected_id
            if row["queue_status"] in {"ELIGIBLE_RESUME", "ELIGIBLE_NEW"} and not row["selected"]:
                row["reasons"].append("LOWER_QUEUE_PRIORITY_THAN_SELECTED")
        return {
            "schema_version": "1.0",
            "catalogue_count": len(books),
            "selected_book": selected_id,
            "selection_policy": "RESUME_THEN_PRIORITY_THEN_STABLE_BOOK_ID",
            "fixture_mode": self.fixture_mode,
            "entries": sorted(rows, key=lambda item: (item["priority"], item["book_id"])),
        }


class AutonomousFactoryDirector:
    """Coordinate supported work until the next honest blocker or completion."""

    def __init__(self, host, runtime_root=None):
        self.host = host
        self.root = host.root
        self.production_books_root = host.books_root
        configured = host._configuration()["runtime_directory"]
        self.runtime_root = Path(runtime_root) if runtime_root else self.root / configured / "orchestration-pr9"

    def _books_root(self, fixture_mode):
        return self.runtime_root / "fixture-books" if fixture_mode else self.production_books_root

    def _run_path(self, books_root, book_id):
        return Path(books_root) / book_id / "orchestration" / "run.json"

    def _initial_run(self, book_id, fixture_mode):
        return {
            "schema_version": "1.0",
            "book_id": book_id,
            "fixture_mode": bool(fixture_mode),
            "publication_eligible": False,
            "current_stage": "SOURCE_CHECK",
            "completed_stages": [],
            "dimensions": {
                "source_readiness": "NOT_EVALUATED",
                "private_production_clearance": "NOT_EVALUATED",
                "editorial_certification": "NOT_EVALUATED",
                "visual_completion": "NOT_STARTED",
                "publication_clearance": "BLOCKED",
                "publication_artifact_readiness": "NOT_READY",
            },
            "blocked": [],
            "updated_at": utc_now(),
        }

    def _load_run(self, books_root, book_id, fixture_mode):
        path = self._run_path(books_root, book_id)
        if path.is_file():
            run = load_json(path)
            if bool(run.get("fixture_mode")) != bool(fixture_mode):
                raise ContractError("fixture and production orchestration state cannot be mixed")
            return run
        if not fixture_mode:
            legacy_path = Path(books_root) / book_id / "run" / "events.jsonl"
            run = self._initial_run(book_id, False)
            if legacy_path.is_file():
                state = StateStore(books_root, book_id).load()
                run["current_stage"] = state["current_stage"]
                run["completed_stages"] = list(state["completed_stages"])
                status_path = Path(books_root) / book_id / "production-status.json"
                if status_path.is_file():
                    status = load_json(status_path)
                    run["dimensions"].update({
                        "source_readiness": status.get("source_readiness", "NOT_EVALUATED"),
                        "private_production_clearance": status.get("private_draft_gate", "NOT_EVALUATED"),
                        "editorial_certification": status.get("independent_editorial_review", "NOT_EVALUATED"),
                        "visual_completion": status.get("visual_production", "NOT_STARTED"),
                        "publication_clearance": status.get("publication_readiness", "BLOCKED"),
                        "publication_artifact_readiness": (
                            "READY" if status.get("exact_result") == "READY_FOR_PUBLICATION" else "NOT_READY"
                        ),
                    })
            return run
        return self._initial_run(book_id, True)

    def _save_run(self, books_root, run):
        run = deepcopy(run)
        run["updated_at"] = utc_now()
        run["run_hash"] = content_hash({key: value for key, value in run.items() if key != "run_hash"})
        atomic_json_write(self._run_path(books_root, run["book_id"]), run)
        return run

    def queue(self, fixture_mode=False):
        return ProductionQueue(self.host.catalogue, self._books_root(fixture_mode), fixture_mode).evaluate()

    def blocked(self, fixture_mode=False):
        queue = self.queue(fixture_mode)
        return {
            "schema_version": "1.0",
            "fixture_mode": bool(fixture_mode),
            "blocked": [row for row in queue["entries"] if row["queue_status"] in {"BLOCKED", "EXCLUDED"}],
        }

    def approvals(self, fixture_mode=False):
        books_root = self._books_root(fixture_mode)
        records = []
        for path in sorted(Path(books_root).glob("*/approvals/*.json")):
            records.append(load_json(path))
        records.extend(ApprovalStore(Path(books_root) / "_approvals").list())
        pending = []
        for row in self.queue(fixture_mode)["entries"]:
            if row["current_stage"] == "AWAITING_STYLE_APPROVAL" or "STYLE_APPROVAL_UNAVAILABLE" in row["reasons"]:
                pending.append({"book_id": row["book_id"], "approval_type": "BOOK_OR_COLLECTION_STYLE", "status": "PENDING"})
        if not fixture_mode:
            for path in sorted(Path(books_root).glob("*/production-integration-status.json")):
                status = load_json(path)
                if status.get("generation_authorized") is False:
                    blocker = next(
                        (item for item in status.get("blockers", []) if item.get("code") == "PR10_CAMPAIGN_AUTHORIZATION_REQUIRED"),
                        {},
                    )
                    pending.append({
                        "book_id": status["book_id"],
                        "approval_type": "PRODUCTION_CAMPAIGN",
                        "campaign_id": status["campaign_id"],
                        "subject_hash": blocker.get("subject_hash"),
                        "request_record_hash": blocker.get("request_record_hash"),
                        "status": "PENDING",
                    })
        return {"schema_version": "1.0", "records": records, "pending": pending, "fixture_mode": bool(fixture_mode)}

    def costs(self, fixture_mode=False):
        books_root = self._books_root(fixture_mode)
        jobs = []
        for path in sorted(Path(books_root).glob("*/orchestration/jobs/*.json")):
            jobs.append(load_json(path))
        estimated = sum(item.get("cost", {}).get("estimated_minor_units") or 0 for item in jobs)
        actual = sum(item.get("cost", {}).get("actual_minor_units") or 0 for item in jobs)
        production_slices = []
        if not fixture_mode:
            for path in sorted(Path(books_root).glob("*/production-integration-status.json")):
                status = load_json(path)
                production_slices.append({
                    "book_id": status["book_id"], "campaign_id": status["campaign_id"],
                    "actual_minor_units": status.get("actual_cost_minor_units", 0),
                    "actual_image_operations": status.get("actual_image_operations", 0),
                })
        return {
            "schema_version": "1.0", "currency": "USD", "fixture_mode": bool(fixture_mode),
            "estimated_minor_units": estimated,
            "actual_minor_units": actual + sum(item["actual_minor_units"] for item in production_slices),
            "paid_calls_executed": sum(bool(item.get("cost", {}).get("paid_call_executed")) for item in jobs),
            "jobs": [{"job_id": item["job_id"], "book_id": item["book_id"], "stage": item["stage"], "cost": item["cost"]} for item in jobs],
            "production_slices": production_slices,
        }

    def status(self):
        queue = self.queue(False)
        counts = {}
        for row in queue["entries"]:
            counts[row["queue_status"]] = counts.get(row["queue_status"], 0) + 1
        return {
            "implementation": "FOUNDATION_PR9",
            "autonomous_execution": {
                stage: {
                    "execution_kind": EXECUTION_KINDS[stage],
                    "worker": WORKERS[stage],
                    "specialist_roles": SPECIALIST_ROLES[stage],
                }
                for stage in ORCHESTRATED_STAGES
            },
            "queue": {"catalogue_count": queue["catalogue_count"], "selected_book": queue["selected_book"], "counts": counts},
            "costs": self.costs(False),
            "publication": "PREPARATION_ONLY_NO_PUBLISH_OR_DEPLOY",
        }

    def _fixture_plan(self, path):
        if not path:
            path = self.root / "book-factory" / "fixtures" / "autonomous-orchestration" / "lifecycle-plan.json"
        plan = load_json(Path(path))
        if plan.get("fixture") is not True or plan.get("publication_eligible") is not False:
            raise ContractError("orchestration fixture plan must be explicitly non-production")
        if set(plan.get("stages", {})) != set(ORCHESTRATED_STAGES):
            raise ContractError("fixture plan must declare every lifecycle stage")
        return plan

    def _input_hashes(self, run, stage, plan=None):
        prior = run.get("stage_outputs", {})
        index = _stage_index(stage)
        earlier = [prior[name] for name in STAGES[1:index] if name in prior]
        seed = content_hash({"book_id": run["book_id"], "stage": stage, "fixture": bool(plan)})
        return [seed, *earlier[-3:]]

    def _fixture_stage(self, run, stage, plan, ledger, books_root):
        spec = plan["stages"][stage]
        worker = {
            "id": spec["worker_id"], "role": WORKERS[stage], "version": spec.get("worker_version", "fixture-1"),
            "independent_from": spec.get("independent_from", []),
        }
        if stage == "EDITORIAL_QA":
            worker["reviewer_ids"] = spec.get("reviewer_ids", [])
        policy_hash = content_hash(plan.get("policy", {}))
        spending_policy = load_json(self.root / "book-factory" / "policies" / "spending-policy.json")
        estimate = spec.get("estimated_cost_minor_units", 0)
        BudgetGuard(spending_policy).reserve(
            stable_id("fixture-cost-reservation", run["book_id"], stage, *self._input_hashes(run, stage, plan)),
            estimate,
        )
        record, reused = ledger.begin(stage, self._input_hashes(run, stage, plan), [policy_hash], worker,
                                      provider_config_hash=spec.get("provider_config_hash", "fixture"),
                                      estimated_cost_minor_units=estimate,
                                      max_attempts=(
                                          self.host._configuration()["retry_limits"]["provider"]
                                          if stage in PROVIDER_STAGES else
                                          self.host._configuration()["retry_limits"]["stage"]
                                      ))
        if reused:
            return record, True
        if spec.get("interrupt_once") and not any(event["event_type"] == "JOB_INTERRUPTED" and event["stage"] == stage for event in ledger.events()):
            return ledger.interrupt(record, "explicit fixture interruption"), False
        result = spec["result"]
        if result not in RESULTS:
            raise ContractError("fixture result is invalid")
        if stage in INDEPENDENT_STAGES:
            earlier_creator = plan["stages"]["MANUSCRIPT" if stage == "EDITORIAL_QA" else "PDF_LAYOUT"]["worker_id"]
            if worker["id"] == earlier_creator:
                result = "ESCALATE"
                spec = dict(spec)
                spec["recovery"] = {"action": "ASSIGN_INDEPENDENT_REVIEWER", "reason": "fixture reviewer matches creator"}
        if stage == "EDITORIAL_QA":
            reviewer_ids = spec.get("reviewer_ids", [])
            writer_id = plan["stages"]["MANUSCRIPT"]["worker_id"]
            if len(set(reviewer_ids)) != 2 or writer_id in reviewer_ids:
                result = "ESCALATE"
                spec = dict(spec)
                spec["recovery"] = {
                    "action": "ASSIGN_TWO_INDEPENDENT_EDITORIAL_REVIEWERS",
                    "reason": "family-reader and theological/source reviewer independence is not established",
                }
        output_payload = {
            "fixture": True, "publication_eligible": False, "book_id": run["book_id"], "stage": stage,
            "job_id": record["job_id"], "input_hashes": record["input_hashes"], "declared_outcome": result,
            "label": "SYNTHETIC ORCHESTRATION ACCEPTANCE FIXTURE - NOT A KHATAKSHETRA PUBLICATION",
        }
        output_hashes = []
        receipt_extra = {}
        if stage == "LETTERING":
            exact = plan.get("exact_lettering", [])
            output_payload["exact_lettering"] = exact
            output_payload["exact_lettering_hash"] = content_hash(exact)
        if stage == "PDF_LAYOUT" and result == "PASS":
            render_root = self.runtime_root / "fixture-render" / run["book_id"]
            manifest_path = self.root / plan["page_fixture_manifest"]
            composition = compose_book(
                load_json(manifest_path), self.root, render_root, True,
                self.root / "book-factory" / "config" / "page-renderer-fonts.json",
            )
            pdf_path = render_root / "synthetic-orchestration-acceptance.pdf"
            pdf_result = export_pdf(load_json(Path(composition["manifest"])), pdf_path, True)
            inspection = inspect_pdf(pdf_path, load_json(Path(composition["manifest"])))
            if inspection["result"] != "PASS":
                result = "FIX"
            output_payload["pdf"] = {
                "sha256": pdf_result["pdf_sha256"], "page_count": inspection["page_count"],
                "inspection_result": inspection["result"], "path": str(pdf_path),
            }
            receipt_extra["pdf_inspection_hash"] = content_hash(inspection)
        artifact = ArtifactStore(books_root).put(
            json.dumps(output_payload, sort_keys=True, ensure_ascii=False).encode("utf-8"),
            media_type="application/json", extension="json", logical_id="%s-%s" % (run["book_id"], stage.lower()),
            input_hashes=record["input_hashes"], version=record["attempt_number"],
        )
        output_hashes.append(artifact["sha256"])
        receipt = {
            "mechanism": "EXPLICIT_SYNTHETIC_FIXTURE_OUTCOME",
            "executed_by": worker["id"],
            "fixture": True,
            "real_provider_call": False,
            "paid_api_calls": 0,
            "input_hashes": record["input_hashes"],
            "output_hashes": output_hashes,
            "specialist_ids": worker.get("reviewer_ids", [worker["id"]]),
            **receipt_extra,
        }
        recovery = spec.get("recovery") if result != "PASS" else None
        completed = ledger.finish(record, result, output_hashes, receipt, 0, recovery)
        return completed, False

    def _production_blockers(self, book_id, run):
        book = self.host.catalogue.get(book_id)
        if book_id == "DM08" or book.get("edition_status") == "EXISTING_EDITION":
            return [{"code": "EXISTING_EDITION_AUTOMATIC_PRODUCTION_EXCLUDED", "owner": "catalogue"}]
        status_path = self.production_books_root / book_id / "production-status.json"
        if status_path.is_file():
            status = load_json(status_path)
            if "RETRY_EXHAUSTED" in status.get("exact_result", ""):
                return [
                    {"code": "PR6_IMAGE_ATTEMPT_BUDGET_EXHAUSTED", "owner": "illustration-producer", "reset_allowed": False},
                    {"code": "PR7_RECOVERY_NOT_AUTHORIZED", "owner": "human-approver"},
                    {"code": "HUMAN_STYLE_APPROVAL_UNAVAILABLE", "owner": "human-approver"},
                    *[{"code": item, "owner": "publication-gate"} for item in status.get("publication_blockers", [])],
                ]
        stage = run["current_stage"]
        if stage in CODEX_STAGES:
            return [{
                "code": "ACTIVE_CODEX_SPECIALIST_EXECUTION_REQUIRED",
                "owner": WORKERS[stage],
                "message": "repository code persisted the exact handoff; the active Codex runtime must execute and import it",
            }]
        if stage in PROVIDER_STAGES:
            return [{"code": "APPROVED_EXTERNAL_IMAGE_PROVIDER_REQUIRED", "owner": WORKERS[stage]}]
        if stage in HUMAN_STAGES:
            return [{"code": "HUMAN_AUTHORIZATION_REQUIRED", "owner": WORKERS[stage]}]
        if stage == "SOURCE_CHECK":
            return [{"code": "SOURCE_AND_PRIVATE_DRAFT_CLEARANCE_REQUIRED", "owner": "source-evidence"}]
        if stage == "LETTERING":
            return [{"code": "APPROVED_ILLUSTRATIONS_AND_EXACT_PAGE_SCRIPTS_REQUIRED", "owner": WORKERS[stage]}]
        if stage == "PDF_LAYOUT":
            return [{"code": "COMPLETE_HASH_BOUND_COMPOSED_PAGE_MANIFEST_REQUIRED", "owner": WORKERS[stage]}]
        if stage == "READY_FOR_PUBLICATION":
            return [{"code": "INDEPENDENT_VISUAL_QA_AND_PUBLICATION_CLEARANCE_REQUIRED", "owner": WORKERS[stage]}]
        return []

    def _persist_production_handoff(self, run, ledger, books_root):
        stage = run["current_stage"]
        worker = {"id": WORKERS[stage], "role": WORKERS[stage], "version": "pr9"}
        input_hashes = self._input_hashes(run, stage)
        record, reused = ledger.begin(stage, input_hashes, [], worker)
        handoff = {
            "schema_version": "1.0", "book_id": run["book_id"], "stage": stage, "job_id": record["job_id"],
            "execution_kind": EXECUTION_KINDS[stage], "required_role": WORKERS[stage],
            "required_specialist_roles": SPECIALIST_ROLES[stage],
            "locked_input_hashes": input_hashes,
            "prerequisites": ["validate exact inputs", "validate schema", "record exact output hashes", "return PASS, FIX or ESCALATE"],
            "independence_required": stage in INDEPENDENT_STAGES,
            "programmatic_codex_spawn_available_inside_repository": False,
            "publication_authorization": False,
        }
        handoff["handoff_hash"] = content_hash(handoff)
        handoff_path = Path(books_root) / run["book_id"] / "orchestration" / "handoffs" / (record["job_id"] + ".json")
        if not handoff_path.is_file():
            atomic_json_write(handoff_path, handoff)
        blockers = self._production_blockers(run["book_id"], run)
        if not blockers and stage == "SOURCE_CHECK":
            blockers = [{"code": "SOURCE_AND_PRIVATE_DRAFT_CLEARANCE_REQUIRED", "owner": "source-evidence"}]
        recovery = {"action": "SATISFY_STAGE_HANDOFF_AND_RESUME", "handoff_path": str(handoff_path), "blockers": blockers}
        if record["status"] == "RUNNING":
            record = ledger.finish(record, "ESCALATE", [handoff["handoff_hash"]], {
                "mechanism": "REPOSITORY_HANDOFF_PREPARATION",
                "executed_by": "autonomous-director",
                "handoff_hash": handoff["handoff_hash"],
                "provider_or_specialist_executed": False,
            }, 0, recovery)
        run["blocked"] = blockers
        return record, handoff_path

    def _execute_production_source_check(self, run, ledger):
        """Execute the read-only source gate and bind any private-draft clearance."""

        book_id = run["book_id"]
        book = self.host.catalogue.get(book_id)
        dossier = self.host.source_dossier(book_id, write=False)
        rules = rules_status(self.root)
        mapping_hash = content_hash(self.host.mappings.resolve(book_id))
        manifest_hash = content_hash(book)
        record, reused = ledger.begin(
            "SOURCE_CHECK",
            [manifest_hash, mapping_hash, dossier["dossier_hash"], dossier["graph_hash"]],
            [rules["sha256"]] if rules.get("sha256") else [],
            {"id": "source-evidence", "role": "source-evidence", "version": "pr9"},
            max_attempts=self.host._configuration()["retry_limits"]["stage"],
        )
        if reused:
            run["dimensions"]["source_readiness"] = dossier["status"]
            run["dimensions"]["private_production_clearance"] = "PASS"
            run["current_stage"] = "MANUSCRIPT"
            return record, run
        blockers = [item["code"] for item in dossier.get("blockers", [])]
        blockers.extend(item["code"] for item in dossier.get("unresolved_flags", []))
        clearance = None
        try:
            clearance = self.host.clearances.latest(book_id)
            validate_private_draft_clearance(clearance, dossier, dossier["story_packets"])
        except ContractError as exc:
            blockers.append("PRIVATE_DRAFT_CLEARANCE_MISSING_OR_STALE")
            clearance_error = str(exc)
        else:
            clearance_error = None
        privately_eligible = (
            clearance is not None
            and dossier.get("controlled_pilot_eligibility") != "NOT_ELIGIBLE"
            and rules.get("status") == "AVAILABLE"
        )
        receipt = {
            "mechanism": "REPOSITORY_READ_ONLY_SOURCE_CHECK",
            "executed_by": "source-evidence",
            "graph_hash": dossier["graph_hash"],
            "dossier_hash": dossier["dossier_hash"],
            "mapping_hash": mapping_hash,
            "rules_hash": rules.get("sha256"),
            "clearance_hash": clearance.get("clearance_hash") if clearance else None,
            "clearance_error": clearance_error,
            "source_graph_mutated": False,
        }
        if not privately_eligible:
            recovery = {
                "action": "RESOLVE_SOURCE_AND_PRIVATE_DRAFT_CLEARANCE",
                "blockers": sorted(set(blockers)),
                "publication_clearance_unchanged": "BLOCKED",
            }
            record = ledger.finish(record, "ESCALATE", [dossier["dossier_hash"]], receipt, 0, recovery)
            run["dimensions"]["source_readiness"] = dossier["status"]
            run["dimensions"]["private_production_clearance"] = "BLOCKED"
            run["blocked"] = [{"code": code, "owner": "source-evidence"} for code in sorted(set(blockers))]
            return record, run
        record = ledger.finish(
            record, "PASS", [dossier["dossier_hash"], clearance["clearance_hash"]], receipt, 0,
        )
        run["dimensions"]["source_readiness"] = dossier["status"]
        run["dimensions"]["private_production_clearance"] = "PASS_PUBLICATION_BLOCKED"
        run["completed_stages"].append("SOURCE_CHECK")
        run.setdefault("stage_outputs", {})["SOURCE_CHECK"] = record["output_hashes"][0]
        run["current_stage"] = "MANUSCRIPT"
        run["blocked"] = []
        return record, run

    def produce_book(self, book_id, fixture_mode=False, fixture_plan_path=None):
        book = self.host.catalogue.get(book_id)
        if book is None:
            raise ContractError("book is not in the selected catalogue", {"book_id": book_id})
        if fixture_mode and not book.get("fixture_private_production_eligible"):
            raise ContractError("fixture execution requires explicit fixture eligibility")
        books_root = self._books_root(fixture_mode)
        run = self._load_run(books_root, book_id, fixture_mode)
        ledger = JobLedger(books_root, book_id, fixture_mode)
        if not fixture_mode:
            blockers = self._production_blockers(book_id, run)
            if blockers and run["current_stage"] == "ART_PROOFS":
                if book_id == "DM04":
                    integration = self.host.prepare_production_slice(book_id)
                    integration["legacy_run"] = run
                    integration["jobs"] = ledger.jobs()
                    integration["blocker_source"] = integration["approval_request_path"]
                    return integration
                run["blocked"] = blockers
                return {
                    "status": "ESCALATE", "book_id": book_id, "run": run, "jobs": ledger.jobs(),
                    "mutated": False, "mutated_art": False,
                    "blocker_source": str(self.production_books_root / book_id / "production-status.json"),
                }
            lease = BookLease(self.runtime_root / "leases")
            owner = "autonomous-director-production"
            lease.acquire(book_id, owner)
            try:
                source_job = None
                if run["current_stage"] == "SOURCE_CHECK":
                    source_job, run = self._execute_production_source_check(run, ledger)
                    if source_job["result"] != "PASS":
                        run = self._save_run(books_root, run)
                        return {
                            "status": "ESCALATE", "book_id": book_id, "current_stage": "SOURCE_CHECK",
                            "job": source_job, "run": run, "mutated_art": False,
                        }
                record, path = self._persist_production_handoff(run, ledger, books_root)
                run = self._save_run(books_root, run)
            finally:
                lease.release(book_id, owner)
            return {
                "status": record["result"], "book_id": book_id, "current_stage": run["current_stage"],
                "job": record, "source_job": source_job, "handoff_path": str(path), "run": run, "mutated_art": False,
            }

        plan = self._fixture_plan(fixture_plan_path)
        if book_id not in plan["eligible_book_ids"]:
            raise ContractError("fixture plan does not authorize this synthetic book")
        lease = BookLease(self.runtime_root / "leases")
        owner = "autonomous-director-fixture"
        lease.acquire(book_id, owner)
        trace = []
        try:
            while run["current_stage"] in ORCHESTRATED_STAGES:
                stage = run["current_stage"]
                record, reused = self._fixture_stage(run, stage, plan, ledger, books_root)
                trace.append({"stage": stage, "job_id": record["job_id"], "result": record["result"], "reused": reused, "status": record["status"]})
                if record["status"] == "INTERRUPTED" or record["result"] != "PASS":
                    run["blocked"] = [{"code": "JOB_INTERRUPTED" if record["status"] == "INTERRUPTED" else "STAGE_REQUIRES_RECOVERY", "job_id": record["job_id"]}]
                    break
                run.setdefault("stage_outputs", {})[stage] = record["output_hashes"][0]
                if stage not in run["completed_stages"]:
                    run["completed_stages"].append(stage)
                if stage == "SOURCE_CHECK":
                    run["dimensions"]["source_readiness"] = "PASS_FIXTURE_ONLY"
                    run["dimensions"]["private_production_clearance"] = "PASS_FIXTURE_ONLY"
                elif stage == "EDITORIAL_QA":
                    run["dimensions"]["editorial_certification"] = "PASS_FIXTURE_ONLY_INDEPENDENT"
                elif stage in {"ART_PROOFS", "ILLUSTRATION", "LETTERING", "PDF_LAYOUT"}:
                    run["dimensions"]["visual_completion"] = "%s_PASS_FIXTURE_ONLY" % stage
                elif stage == "VISUAL_QA":
                    run["dimensions"]["visual_completion"] = "PASS_FIXTURE_ONLY_IMAGE_CAPABLE_REVIEW"
                elif stage == "READY_FOR_PUBLICATION":
                    run["dimensions"]["publication_artifact_readiness"] = "PASS_FIXTURE_ONLY_NOT_PUBLICATION"
                index = _stage_index(stage)
                run["current_stage"] = STAGES[index + 1] if index + 1 < len(STAGES) else "READY_FOR_PUBLICATION"
                run["blocked"] = []
                if stage == "READY_FOR_PUBLICATION":
                    break
            run = self._save_run(books_root, run)
        finally:
            lease.release(book_id, owner)
        final = run["current_stage"] == "READY_FOR_PUBLICATION" and "READY_FOR_PUBLICATION" in run["completed_stages"]
        return {
            "status": "FIXTURE_LIFECYCLE_COMPLETE" if final else "INTERRUPTED" if run["blocked"] and run["blocked"][0]["code"] == "JOB_INTERRUPTED" else "ESCALATE",
            "book_id": book_id, "fixture": True, "publication_eligible": False,
            "run": run, "trace": trace, "jobs": ledger.jobs(),
        }

    def resume_book(self, book_id, fixture_mode=False, fixture_plan_path=None):
        return self.produce_book(book_id, fixture_mode, fixture_plan_path)

    def produce_next(self, fixture_mode=False, fixture_plan_path=None, select_only=False):
        queue = self.queue(fixture_mode)
        if not queue["selected_book"]:
            return {"status": "NO_ELIGIBLE_BOOKS", "queue": queue, "mutated": False}
        if select_only:
            return {"status": "DRY_RUN", "selected_book": queue["selected_book"], "queue": queue, "mutated": False}
        result = self.produce_book(queue["selected_book"], fixture_mode, fixture_plan_path)
        result["selection"] = next(row for row in queue["entries"] if row["book_id"] == queue["selected_book"])
        return result
