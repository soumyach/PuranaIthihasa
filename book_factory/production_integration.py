"""PR10/PR11 real-production slice integration and fail-closed execution gates.

The repository can select and bind real DM04 inputs, persist a campaign request,
validate authorization, prepare exact reference-conditioned provider requests,
and validate independent-review contracts.  It cannot grant the campaign
authority, invoke the session-only host image tool, or make semantic judgments.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from .approvals import ApprovalStore
from .errors import ContractError
from .illustration_production import inspect_png
from .orchestration import route_page_repair, validate_reference_receipt
from .util import atomic_json_write, content_hash, load_json, sha256_bytes, utc_now
from .versioning import ImmutableVersionStore


BOOK_ID = "DM04"
CAMPAIGN_ID = "dm04-pr10-real-production-slice-01"
SELECTED_PAGE_IDS = (
    "page-27d143ae995bf60742b65c5b",
    "page-5316f7271234e4ab31991528",
)
PAGE_SCRIPT_PATHS = {
    SELECTED_PAGE_IDS[0]: "books/DM04/page-scripts/page-0001.v0003.json",
    SELECTED_PAGE_IDS[1]: "books/DM04/page-scripts/page-0004.v0003.json",
}
PAGE_ROLES = {
    SELECTED_PAGE_IDS[0]: "DIALOGUE_SEQUENTIAL",
    SELECTED_PAGE_IDS[1]: "DIVINE_MANIFESTATION_IMMERSIVE",
}
EXPECTED_PAGE_FACTS = {
    SELECTED_PAGE_IDS[0]: {
        "page_number": 1,
        "event_ids": ["dm-event-008"],
        "layout_type": "TWO_PANEL",
        "characters": ["dm-medhas", "dm-suratha", "dm-samadhi"],
    },
    SELECTED_PAGE_IDS[1]: {
        "page_number": 4,
        "event_ids": ["dm-event-009"],
        "layout_type": "FULL_PAGE",
        "characters": ["dm-devi"],
    },
}
REVIEW_DIMENSIONS = (
    "SOURCE_FIDELITY",
    "RELIGIOUS_ICONOGRAPHY",
    "CULTURAL_AUTHENTICITY",
    "CHARACTER_CONTINUITY",
    "NARRATIVE_CLARITY",
    "ARTISTIC_QUALITY",
    "LETTERING_READABILITY",
    "COMPOSITION",
    "REFERENCE_ALIGNMENT",
)


def _unsigned_hash(record, hash_field):
    return content_hash({key: value for key, value in record.items() if key != hash_field})


def _write_if_changed(path, value):
    path = Path(path)
    if path.is_file() and load_json(path) == value:
        return False
    atomic_json_write(path, value)
    return True


def validate_real_image_review(request, response):
    """Validate independence and actual-pixel evidence without judging pixels."""

    if response.get("image_sha256") != request.get("image_sha256"):
        raise ContractError("production review does not bind the exact image")
    reviewer = response.get("reviewer", {})
    if not reviewer.get("image_capable") or not reviewer.get("inspected_actual_pixels"):
        return {"result": "ESCALATE", "code": "ACTUAL_PIXEL_REVIEW_NOT_EXECUTED"}
    if reviewer.get("reading_size") != "ACTUAL_READING_SIZE":
        return {"result": "ESCALATE", "code": "ACTUAL_READING_SIZE_NOT_INSPECTED"}
    if reviewer.get("id") in set(request.get("producer_ids", [])):
        return {"result": "ESCALATE", "code": "REVIEWER_NOT_INDEPENDENT_FROM_PRODUCER"}
    assessments = response.get("assessments", [])
    if [item.get("dimension") for item in assessments] != list(REVIEW_DIMENSIONS):
        return {"result": "ESCALATE", "code": "REVIEW_DIMENSIONS_INCOMPLETE_OR_OUT_OF_ORDER"}
    results = [item.get("result") for item in assessments]
    if any(value not in {"PASS", "FIX", "ESCALATE"} for value in results):
        raise ContractError("production review contains an invalid dimension result")
    result = "ESCALATE" if "ESCALATE" in results else "FIX" if "FIX" in results else "PASS"
    findings = response.get("findings", [])
    if result != "PASS" and not findings:
        raise ContractError("non-PASS production review requires specific findings")
    for finding in findings:
        required = {"dimension", "discrepancy", "evidence", "repair_type", "page_id"}
        if required - set(finding):
            raise ContractError("production review finding lacks localized repair evidence")
        if finding["page_id"] != request.get("page_id"):
            raise ContractError("production review finding targets a different page")
    return {
        "result": result,
        "review_hash": content_hash(response),
        "image_sha256": request["image_sha256"],
        "page_id": request["page_id"],
        "independent_actual_pixel_review": True,
        "findings": findings,
    }


class RealProductionSlice:
    """Prepare, execute through the host boundary, and review the bounded DM04 slice."""

    def __init__(self, repository_root):
        self.root = Path(repository_root).resolve()
        self.books_root = self.root / "books"
        self.book_root = self.books_root / BOOK_ID
        self.slice_store = ImmutableVersionStore(self.books_root, "production-slices")
        self.request_store = ImmutableVersionStore(self.books_root, "production-campaign-requests")
        self.approvals = ApprovalStore(self.book_root / "approvals")
        self.status_path = self.book_root / "production-integration-status.json"

    def _store(self, kind, page_id):
        return ImmutableVersionStore(self.books_root, "%s/%s" % (kind, page_id))

    def _latest_by_page(self, kind):
        result = {}
        for page_id in SELECTED_PAGE_IDS:
            versions = self._store(kind, page_id).versions(BOOK_ID)
            if len(versions) > 1:
                raise ContractError("PR11 one-operation ceiling was exceeded", {
                    "kind": kind, "page_id": page_id, "versions": len(versions),
                })
            if versions:
                result[page_id] = versions[-1]
        return result

    def _asset(self, relative_path, logical_hash=None, role=None):
        path = self.root / relative_path
        if not path.is_file():
            raise ContractError("required PR10 real input is missing", {"path": relative_path})
        result = {
            "path": relative_path,
            "sha256": sha256_bytes(path.read_bytes()),
            "bytes": path.stat().st_size,
        }
        if logical_hash:
            result["logical_hash"] = logical_hash
        if role:
            result["role"] = role
        return result

    def _recovery_campaign(self):
        records = ImmutableVersionStore(self.books_root, "proof-recovery-requests").versions(BOOK_ID)
        if not records:
            raise ContractError("PR10 requires the immutable PR7 recovery campaign")
        campaign = records[-1]["payload"]
        if campaign.get("generation_authorized") is not False:
            raise ContractError("PR7 recovery history no longer has its fail-closed authorization state")
        history = campaign.get("pr6_history", {})
        if history.get("retry_ceiling_exhausted") is not True or history.get("counter_reset") is not False:
            raise ContractError("PR6 exhausted counters were not preserved")
        return campaign

    def _page(self, page_id):
        page = load_json(self.root / PAGE_SCRIPT_PATHS[page_id])
        expected = EXPECTED_PAGE_FACTS[page_id]
        if page.get("page_id") != page_id or page.get("page_number") != expected["page_number"]:
            raise ContractError("selected PR10 page identity is stale", {"page_id": page_id})
        if page.get("event_ids") != expected["event_ids"]:
            raise ContractError("selected PR10 page source events changed", {"page_id": page_id})
        if page.get("layout", {}).get("type") != expected["layout_type"]:
            raise ContractError("selected PR10 page layout changed", {"page_id": page_id})
        if not set(expected["characters"]).issubset(page.get("character_ids", [])):
            raise ContractError("selected PR10 page character constraints changed", {"page_id": page_id})
        lettering = page.get("lettering", [])
        if not lettering or any(not item.get("id") or not item.get("text") for item in lettering):
            raise ContractError("selected PR10 page lacks exact editable lettering", {"page_id": page_id})
        return page

    def _recovery_request(self, campaign, page_id):
        matches = [item for item in campaign.get("requests", []) if item.get("page_id") == page_id]
        if len(matches) != 1:
            raise ContractError("selected PR10 page must bind one PR7 recovery request", {"page_id": page_id})
        request = deepcopy(matches[0])
        path = self.root / request["page_script_path"]
        if sha256_bytes(path.read_bytes()) != request["page_script_sha256"]:
            raise ContractError("PR7 recovery request page-script hash is stale", {"page_id": page_id})
        return request

    def _references(self, request):
        references = []
        for item in request.get("reference_package", []):
            reference = {
                "role": item["role"],
                "reference_id": item.get("reference_id"),
                "path": item.get("path"),
                "sha256": item.get("sha256"),
                "use": item.get("use"),
                "content_transfer": item.get("content_transfer"),
                "available": bool(item.get("path") and item.get("sha256")),
            }
            if reference["available"]:
                path = self.root / reference["path"]
                if not path.is_file() or sha256_bytes(path.read_bytes()) != reference["sha256"]:
                    raise ContractError("PR10 reference input is missing or stale", {
                        "page_id": request["page_id"], "role": reference["role"],
                    })
            references.append(reference)
        required_roles = {
            "REFERENCE_A_SERIES_VISUAL_IDENTITY",
            "REFERENCE_B_PAGE_COMPOSITION",
            "REFERENCE_C_CHARACTER_IDENTITY",
            "REFERENCE_D_SETTING_ENVIRONMENT",
        }
        if {item["role"] for item in references} != required_roles or len(references) != 4:
            raise ContractError("PR10 page must resolve each A/B/C/D reference role exactly once")
        return references

    def _failed_image_path(self, image_hash):
        for receipt_path in sorted((self.book_root / "illustration-proofs" / "receipts").glob("*.json")):
            receipt = load_json(receipt_path)
            image = receipt.get("image", {})
            if image.get("sha256") == image_hash:
                path = self.root / image["path"]
                if not path.is_file() or sha256_bytes(path.read_bytes()) != image_hash:
                    raise ContractError("PR6 parent image is missing or stale")
                return image["path"]
        raise ContractError("PR10 edit input does not bind a preserved PR6 image")

    def _selected_pages(self, campaign):
        selected = []
        for page_id in SELECTED_PAGE_IDS:
            page = self._page(page_id)
            recovery = self._recovery_request(campaign, page_id)
            references = self._references(recovery)
            operation = "edit" if page_id == SELECTED_PAGE_IDS[0] else "generate"
            base_image = None
            if operation == "edit":
                base_image = {
                    "path": self._failed_image_path(recovery["parent_pr6"]["image_hash"]),
                    "sha256": recovery["parent_pr6"]["image_hash"],
                    "status": "REJECTED_PR6_EDIT_SOURCE_ONLY_NOT_PAGE_ASSET",
                }
            selected.append({
                "selection_role": PAGE_ROLES[page_id],
                "page_id": page_id,
                "page_number": page["page_number"],
                "title": page["title"],
                "page_script": self._asset(PAGE_SCRIPT_PATHS[page_id], role="LOCKED_PAGE_SCRIPT"),
                "event_ids": deepcopy(page["event_ids"]),
                "source_claim_ids": deepcopy(page["source_claim_ids"]),
                "character_ids": deepcopy(page["character_ids"]),
                "continuity_requirements": deepcopy(page["continuity_requirements"]),
                "location_id": page["location_id"],
                "layout": deepcopy(page["layout"]),
                "panel_count": page["panel_count"],
                "panel_ids": [item["id"] for item in page["panels"]],
                "lettering": deepcopy(page["lettering"]),
                "lettering_hash": content_hash(page["lettering"]),
                "safe_regions": deepcopy(page["safe_regions"]),
                "operation": operation,
                "operation_ceiling": 1,
                "delivery_mode": (
                    "TWO_PANEL_CLEAN_ART_SHEET_WITH_SEPARATELY_REVIEWABLE_PANEL_REGIONS"
                    if page_id == SELECTED_PAGE_IDS[0] else "FULL_PAGE_CLEAN_ART"
                ),
                "base_image": base_image,
                "references": references,
                "reference_package_hash": content_hash(references),
                "principal_action": recovery["principal_action"],
                "prompt": recovery["concise_prompt"],
                "prohibited_transfers": deepcopy(recovery["prohibited_transfers"]),
                "source_iconography_constraints": deepcopy(recovery["source_iconography_constraints"]),
                "cultural_authenticity_constraints": deepcopy(recovery["cultural_authenticity_constraints"]),
                "parent_pr6": deepcopy(recovery["parent_pr6"]),
                "pr6_attempts_preserved": recovery["pr6_attempts_preserved"],
            })
        return selected

    def _backend(self):
        capability_path = "book-factory/config/pr10-session-image-capability.json"
        capability = load_json(self.root / capability_path)
        if capability.get("provider_id") != "codex-built-in-image-gen":
            raise ContractError("PR10 session capability names an unexpected provider")
        if capability.get("reference_input_interface") != "referenced_image_paths":
            raise ContractError("PR10 backend does not expose real reference image inputs")
        if capability.get("repository_programmatic_invocation") is not False:
            raise ContractError("PR10 backend boundary must remain host-session scoped")
        return {
            "record": self._asset(capability_path, role="CURRENT_SESSION_CAPABILITY_INSPECTION"),
            "provider_id": capability["provider_id"],
            "model": capability["model"],
            "host_tool": capability["host_tool"],
            "operations": deepcopy(capability["operations"]),
            "reference_conditioning": capability["reference_conditioning"],
            "reference_input_interface": capability["reference_input_interface"],
            "repository_programmatic_invocation": capability["repository_programmatic_invocation"],
            "current_session_availability": capability["current_session_availability"],
            "direct_monetary_cost": capability["direct_monetary_cost"],
        }
    def _build_plan(self):
        campaign = self._recovery_campaign()
        pages = self._selected_pages(campaign)
        clearance_path = "books/DM04/source-clearance/d43a5f725e4ea595f49a55411eb88af1c65c3d0ca6bf397fdef0d6b7c54f7c7c.json"
        clearance = load_json(self.root / clearance_path)
        if clearance.get("private_draft_gate") != "PRIVATE_DRAFT_PERMITTED_PUBLICATION_BLOCKED":
            raise ContractError("DM04 private-draft clearance changed")
        illustration_blocked = any("illustration" in item.lower() and "blocked" in item.lower()
                                   for item in clearance.get("limitations", []))
        if not illustration_blocked:
            raise ContractError("PR10 expected an explicit illustration-permission boundary")
        production_status = load_json(self.book_root / "production-status.json")
        source_dossier = load_json(self.book_root / "source-readiness" / "75a6d7223209feb8850b482d9e0876cd323991652b436ac139470cadc95041d3.json")
        source_packet = load_json(self.book_root / "story-packets" / "b784b365d9c921312285f453b4f6a4a15a7be935e2f0fdda6cfa8eba12797744.json")
        manuscript = load_json(self.book_root / "manuscripts" / "v0005.json")
        storyboard = load_json(self.book_root / "storyboards" / "v0003.json")
        character_bible = load_json(self.book_root / "character-bibles" / "v0004.json")
        location_bible = load_json(self.book_root / "location-bibles" / "v0002.json")
        typography = load_json(self.book_root / "typography" / "v0003.json")
        locked_inputs = [
            self._asset(clearance_path, clearance["clearance_hash"], "PRIVATE_DRAFT_CLEARANCE"),
            self._asset("books/DM04/source-readiness/75a6d7223209feb8850b482d9e0876cd323991652b436ac139470cadc95041d3.json", source_dossier["dossier_hash"], "SOURCE_DOSSIER"),
            self._asset("books/DM04/story-packets/b784b365d9c921312285f453b4f6a4a15a7be935e2f0fdda6cfa8eba12797744.json", source_packet["packet_hash"], "STORY_PACKET"),
            self._asset("books/DM04/manuscripts/v0005.json", manuscript["content_hash"], "MANUSCRIPT_V5"),
            self._asset("books/DM04/storyboards/v0003.json", storyboard["content_hash"], "STORYBOARD_V3"),
            self._asset("books/DM04/character-bibles/v0004.json", character_bible["content_hash"], "CHARACTER_BIBLE"),
            self._asset("books/DM04/location-bibles/v0002.json", location_bible["content_hash"], "LOCATION_BIBLE"),
            self._asset("books/DM04/typography/v0003.json", typography["content_hash"], "TYPOGRAPHY"),
            self._asset("MYTHOLOGY_COMIC_RULES.md", role="SERIES_RULES"),
            self._asset("book-factory/references/visual-gold-standard/manifest.json", role="VISUAL_GOLD_STANDARD"),
            self._asset("books/DM04/proof-recovery-requests/v0001.json", role="PR7_RECOVERY_HISTORY"),
            self._asset("books/DM04/production-status.json", production_status["status_hash"], "PR6_PRODUCTION_STATUS"),
        ]
        authorization_subject = {
            "campaign_id": CAMPAIGN_ID,
            "book_id": BOOK_ID,
            "purpose": "PRIVATE_INTERNAL_TWO_PAGE_VISUAL_PRODUCTION_TEST",
            "page_ids": list(SELECTED_PAGE_IDS),
            "page_script_sha256": [item["page_script"]["sha256"] for item in pages],
            "reference_package_hashes": [item["reference_package_hash"] for item in pages],
            "operation_ceiling_total": 2,
            "operation_ceiling_per_page": 1,
            "maximum_paid_spend_minor_units": 0,
            "currency": "USD",
            "publication_authorized": False,
            "pr6_counter_reset": False,
            "locked_input_sha256": sorted(item["sha256"] for item in locked_inputs),
        }
        authorization_subject_hash = content_hash(authorization_subject)
        return {
            "schema_version": "1.0",
            "milestone": "PR10",
            "book_id": BOOK_ID,
            "campaign_id": CAMPAIGN_ID,
            "purpose": "REAL_TWO_PAGE_PRODUCTION_INTEGRATION_SLICE",
            "production_scope": "PRIVATE_INTERNAL_ONLY",
            "publication_eligible": False,
            "selected_pages": pages,
            "selection_evidence": {
                "storyboard_page_count": len(storyboard["payload"]["pages"]),
                "selection_count": 2,
                "exact_existing_page_ids": list(SELECTED_PAGE_IDS),
                "replacement_scenes_invented": False,
            },
            "permission_state": {
                "private_manuscript_draft": "PERMITTED_WITH_LIMITATIONS",
                "private_illustration_testing": "NOT_AUTHORIZED_BY_EXISTING_CLEARANCE",
                "publication": clearance["publication_gate"],
                "source_readiness": source_dossier["status"],
                "unresolved_source_flags_preserved": deepcopy(source_dossier["unresolved_flags"]),
                "theological_or_full_arc_publication_review": source_packet["independent_full_arc_review"],
                "evidence": {"clearance_hash": clearance["clearance_hash"], "limitations": deepcopy(clearance["limitations"])},
            },
            "backend": self._backend(),
            "authorization_subject": authorization_subject,
            "authorization_subject_hash": authorization_subject_hash,
            "authorization": {
                "required": True,
                "status": "NOT_GRANTED",
                "approval_type": "PRODUCTION_CAMPAIGN",
                "proposed_operation_ceiling_is_authorization": False,
            },
            "pr6_history": deepcopy(campaign["pr6_history"]),
            "cost_policy": {
                "paid_calls_enabled": False,
                "maximum_paid_spend_minor_units": 0,
                "actual_spend_minor_units": 0,
                "currency": "USD",
                "no_cost_capability_still_requires_campaign_authorization": True,
            },
            "locked_inputs": locked_inputs,
            "artifact_gates": {
                "generation": "BLOCKED_PENDING_SEPARATE_CAMPAIGN_AUTHORIZATION",
                "composition": "BLOCKED_NO_NEW_INDEPENDENTLY_REVIEWED_IMAGES",
                "independent_visual_review": "NOT_EXECUTED_NO_NEW_PIXELS",
                "human_style_approval": "NOT_REACHED",
                "pdf": "NOT_CREATED_ART_AND_REVIEW_GATES_BLOCKED",
            },
            "actual_execution": {
                "real_input_assets_validated": True,
                "image_operations_executed": 0,
                "real_illustrations_generated": 0,
                "composed_pages_created": 0,
                "independent_pixel_reviews_completed": 0,
                "pdfs_created": 0,
                "paid_calls": 0,
                "actual_cost_minor_units": 0,
            },
            "recovery_demonstration": {
                "mode": "ISOLATED_FIXTURE_BECAUSE_NO_REAL_PR10_PAGE_FAILURE_COULD_OCCUR_BEFORE_AUTHORIZATION",
                "fixture_path": "book-factory/fixtures/real-production-integration/page-local-recovery.json",
                "production_assets_modified": False,
            },
            "autonomy": {
                "one_director_invocation_completed": [
                    "real input and hash validation", "two-page selection", "permission evaluation",
                    "backend-interface inspection binding", "reference-package resolution", "campaign approval request preparation",
                ],
                "active_codex_host_after_authorization": ["two bounded image operations"],
                "independent_specialist_after_images": ["actual-pixel source-image and composed-page review"],
                "human_authority": ["PR10 campaign authorization", "exact-asset style approval after independent PASS"],
                "external_or_unavailable": ["repository-native image invocation", "repository-native specialist spawning", "publication"],
                "manual_interventions_completed_in_this_run": 0,
                "manual_interventions_currently_required": 1,
                "minimum_human_decisions_to_internal_proof": 2,
                "fully_autonomous_claim": False,
            },
            "continuous_book_readiness": {
                "queue_continuation": "IMPLEMENTED_PR9_BUT_NO_AUTHORITATIVE_PRODUCTION_READY_NEXT_BOOK",
                "book_level_locking": "IMPLEMENTED_MAX_ONE_ACTIVE_BOOK",
                "budget_limits": "IMPLEMENTED_ZERO_SPEND",
                "style_approval_reuse": "SCOPED_HASH_BOUND_ONLY_NO_REAL_REUSABLE_APPROVAL_PRESENT",
                "character_reference_reuse": "SUPPORTED_BUT_NO_HUMAN_APPROVED_DM04_CHARACTER_IMAGE",
                "interruption_recovery": "IMPLEMENTED_STABLE_JOBS_AND_IMPORT_BOUNDARY",
                "blocked_candidate_skipping": "IMPLEMENTED",
                "per_book_quality_gates": "IMPLEMENTED_FAIL_CLOSED",
                "persistent_results": "IMPLEMENTED_CONTENT_ADDRESSED_AND_IMMUTABLE",
                "next_book_started": False,
            },
        }

    def _approval(self, plan):
        return self.approvals.find_valid(
            "PRODUCTION_CAMPAIGN",
            plan["authorization_subject_hash"],
            {"type": "book", "id": BOOK_ID},
            target_context={"source_scope": "dm-source", "tradition_id": "devi-mahatmyam", "edition_id": "pargiter-1904"},
            current_evidence_hash=plan["authorization_subject_hash"],
        )

    def _approval_request(self, plan_record):
        plan = plan_record["payload"]
        request = {
            "schema_version": "1.0",
            "request_type": "PRODUCTION_CAMPAIGN_AUTHORIZATION",
            "approval_type": "PRODUCTION_CAMPAIGN",
            "book_id": BOOK_ID,
            "campaign_id": CAMPAIGN_ID,
            "subject_type": "PRODUCTION_CAMPAIGN",
            "subject_hash": plan["authorization_subject_hash"],
            "scope": {"type": "book", "id": BOOK_ID},
            "plan_record_hash": plan_record["content_hash"],
            "requested_authority": "PRIVATE_INTERNAL_VISUAL_TESTING_ONLY",
            "requested_operations": [
                {"page_id": item["page_id"], "operation": item["operation"], "maximum_operations": 1}
                for item in plan["selected_pages"]
            ],
            "conditions_required": [
                "PRIVATE_INTERNAL_ONLY", "PUBLICATION_REMAINS_BLOCKED", "ZERO_ADDITIONAL_COST_ONLY",
                "ONE_OPERATION_PER_SELECTED_PAGE", "NO_RETRY_WITHOUT_NEW_APPROVAL", "PR6_COUNTERS_REMAIN_EXHAUSTED",
                "REFERENCE_INPUT_RECEIPT_REQUIRED", "INDEPENDENT_ACTUAL_PIXEL_REVIEW_REQUIRED",
            ],
            "maximum_paid_spend_minor_units": 0,
            "currency": "USD",
            "approval_not_implied_by_this_request": True,
            "instructions": "An authorized human must supply a separate exact-hash approval record. The Director will not infer consent from this milestone or from the two-operation ceiling.",
        }
        request["request_hash"] = _unsigned_hash(request, "request_hash")
        return request

    def _validate_stored(self):
        plans = self.slice_store.versions(BOOK_ID)
        requests = self.request_store.versions(BOOK_ID)
        if not plans or not requests:
            raise ContractError("PR10 production slice has not been prepared")
        expected_plan = self._build_plan()
        matching_plans = [record for record in plans if record["payload"] == expected_plan]
        if not matching_plans:
            raise ContractError("stored PR10 production slice is stale")
        plan_record = matching_plans[-1]
        expected_request = self._approval_request(plan_record)
        matching_requests = [record for record in requests if record["payload"] == expected_request]
        if not matching_requests:
            raise ContractError("stored PR10 campaign request is stale")
        request_record = matching_requests[-1]
        return plan_record, request_record

    def _status(self, plan_record, request_record):
        plan = plan_record["payload"]
        approval = self._approval(plan)
        image_records = self._latest_by_page("production-image-receipts")
        review_records = self._latest_by_page("production-visual-reviews")
        review_results = {
            page_id: record["payload"]["result"] for page_id, record in review_records.items()
        }
        if not approval:
            lifecycle_status = "AWAITING_CAMPAIGN_AUTHORIZATION"
            next_action = "AUTHORIZED_HUMAN_MUST_APPROVE_EXACT_PR10_CAMPAIGN_SUBJECT_HASH"
        elif len(image_records) < len(SELECTED_PAGE_IDS):
            lifecycle_status = "AUTHORIZED_AWAITING_GENERATION"
            next_action = "IMPORT_ONLY_THE_REMAINING_AUTHORIZED_HOST_IMAGE_RESULT"
        elif len(review_records) < len(SELECTED_PAGE_IDS):
            lifecycle_status = "GENERATED_AWAITING_INDEPENDENT_VISUAL_REVIEW"
            next_action = "RUN_INDEPENDENT_ACTUAL_PIXEL_REVIEW"
        elif all(value == "PASS" for value in review_results.values()):
            lifecycle_status = "REVIEWED_PASS_PRIVATE_PREVIEW_ONLY"
            next_action = "HUMAN_STYLE_APPROVAL_REQUIRED_BEFORE_PRODUCTION_ASSET_PROMOTION"
        else:
            lifecycle_status = "REVIEWED_FIX_REQUIRED_CAMPAIGN_COMPLETE_NO_RETRY"
            next_action = "STOP_CAMPAIGN_REVIEW_TARGETED_CORRECTION_REQUESTS"
        blockers = [] if approval else [
            {
                "code": "PR10_CAMPAIGN_AUTHORIZATION_REQUIRED",
                "owner": "authorized-human-approver",
                "subject_hash": plan["authorization_subject_hash"],
                "request_record_hash": request_record["content_hash"],
            },
            {"code": "PRIVATE_ILLUSTRATION_TESTING_NOT_GRANTED_BY_EXISTING_CLEARANCE", "owner": "source-rights-authority"},
            {"code": "PR6_IMAGE_ATTEMPT_BUDGET_EXHAUSTED", "owner": "illustration-producer", "reset_allowed": False},
            {"code": "PR7_RECOVERY_NOT_AUTHORIZED", "owner": "authorized-human-approver"},
            {"code": "HUMAN_STYLE_APPROVAL_UNAVAILABLE", "owner": "authorized-human-approver"},
        ]
        if approval and review_records and any(value != "PASS" for value in review_results.values()):
            blockers.extend({
                "code": "PR11_INDEPENDENT_VISUAL_REVIEW_%s" % record["payload"]["result"],
                "owner": "illustration-producer",
                "page_id": page_id,
                "retry_allowed": False,
            } for page_id, record in review_records.items() if record["payload"]["result"] != "PASS")
        if approval and review_records and all(value == "PASS" for value in review_results.values()):
            blockers.append({
                "code": "HUMAN_STYLE_APPROVAL_UNAVAILABLE",
                "owner": "authorized-human-approver",
                "preview_only_permitted": True,
            })
        unknown_cost = bool(image_records)
        status = {
            "schema_version": "1.0",
            "book_id": BOOK_ID,
            "campaign_id": CAMPAIGN_ID,
            "status": lifecycle_status,
            "plan_record_hash": plan_record["content_hash"],
            "approval_request_record_hash": request_record["content_hash"],
            "approval_request_hash": request_record["payload"]["request_hash"],
            "approval_id": approval.get("id") if approval else None,
            "generation_authorized": bool(approval),
            "selected_page_ids": list(SELECTED_PAGE_IDS),
            "real_input_assets_validated": True,
            "actual_image_operations": len(image_records),
            "authorized_image_operation_ceiling": len(SELECTED_PAGE_IDS),
            "actual_cost_minor_units": None if unknown_cost else 0,
            "actual_cost_status": "UNKNOWN_TOOL_INTERFACE_DOES_NOT_EXPOSE_INCREMENTAL_USD" if unknown_cost else "NOT_INCURRED_NO_OPERATIONS",
            "currency": "USD",
            "purchased_credit_balance_observed": "0",
            "purchased_credit_consumption": "NOT_REQUESTED_OR_REPORTED",
            "separately_billed_provider_calls": 0,
            "illustrations": "%d_REAL_IMAGES_IMPORTED" % len(image_records) if image_records else "NOT_GENERATED",
            "image_hashes": {
                page_id: record["payload"]["image"]["sha256"] for page_id, record in image_records.items()
            },
            "composition": "NOT_CREATED",
            "independent_visual_review": (
                "NOT_EXECUTED" if not review_records else
                "%d_OF_%d_COMPLETE" % (len(review_records), len(SELECTED_PAGE_IDS))
            ),
            "visual_review_results": review_results,
            "localized_recovery": (
                "REAL_PAGE_LOCAL_CORRECTION_REQUESTS_PERSISTED_NO_RETRY"
                if review_records and any(value != "PASS" for value in review_results.values())
                else "ISOLATED_FIXTURE_ONLY"
            ),
            "pdf": "NOT_CREATED_ART_AND_REVIEW_GATES_BLOCKED",
            "publication_eligible": False,
            "publication_status_preserved": "BLOCKED",
            "manual_interventions_currently_required": 0 if lifecycle_status == "REVIEWED_FIX_REQUIRED_CAMPAIGN_COMPLETE_NO_RETRY" else 1,
            "human_interventions_required_for_future_correction": (
                [
                    "QUALIFIED_RELIGIOUS_ICONOGRAPHY_REVIEW_AND_APPROVED_DONOR_IDENTITY_MAP",
                    "SEPARATE_NEW_EXACT_CAMPAIGN_AUTHORIZATION",
                ] if lifecycle_status == "REVIEWED_FIX_REQUIRED_CAMPAIGN_COMPLETE_NO_RETRY" else []
            ),
            "next_required_action": next_action,
            "blockers": blockers,
            "blocked": deepcopy(blockers),
        }
        status["status_hash"] = _unsigned_hash(status, "status_hash")
        return status

    def prepare(self):
        existing_plans = self.slice_store.versions(BOOK_ID)
        existing_requests = self.request_store.versions(BOOK_ID)
        before_plans = len(existing_plans)
        before_requests = len(existing_requests)
        plan = self._build_plan()
        matching_plans = [record for record in existing_plans if record["payload"] == plan]
        if matching_plans:
            plan_record = matching_plans[-1]
        else:
            plan_record = self.slice_store.put(
                BOOK_ID, plan, existing_plans[-1]["content_hash"] if existing_plans else None,
            )
        request = self._approval_request(plan_record)
        matching_requests = [record for record in existing_requests if record["payload"] == request]
        if matching_requests:
            request_record = matching_requests[-1]
        else:
            request_record = self.request_store.put(
                BOOK_ID, request, existing_requests[-1]["content_hash"] if existing_requests else None,
            )
        status = self._status(plan_record, request_record)
        status_changed = _write_if_changed(self.status_path, status)
        mutated = (
            len(self.slice_store.versions(BOOK_ID)) != before_plans
            or len(self.request_store.versions(BOOK_ID)) != before_requests
            or status_changed
        )
        return {
            "status": "ESCALATE" if not status["generation_authorized"] else status["status"],
            "book_id": BOOK_ID,
            "campaign_id": CAMPAIGN_ID,
            "selected_pages": [
                {"page_id": item["page_id"], "page_number": item["page_number"], "title": item["title"], "selection_role": item["selection_role"]}
                for item in plan["selected_pages"]
            ],
            "plan_path": str(self.book_root / "production-slices" / ("v%04d.json" % plan_record["version"])),
            "approval_request_path": str(self.book_root / "production-campaign-requests" / ("v%04d.json" % request_record["version"])),
            "integration_status_path": str(self.status_path),
            "run": status,
            "mutated": mutated,
            "mutated_art": False,
        }

    def status(self):
        plan_record, request_record = self._validate_stored()
        status = self._status(plan_record, request_record)
        if self.status_path.is_file() and load_json(self.status_path) != status:
            raise ContractError("materialized PR10 integration status is stale")
        return {"status": status["status"], "book_id": BOOK_ID, "run": status, "mutated": False}

    def import_campaign_approval(self, approval_path):
        plan_record, request_record = self._validate_stored()
        plan = plan_record["payload"]
        proposed = load_json(Path(approval_path))
        exact = {
            "approval_type": "PRODUCTION_CAMPAIGN",
            "subject_type": "PRODUCTION_CAMPAIGN",
            "subject_hash": plan["authorization_subject_hash"],
            "scope": {"type": "book", "id": BOOK_ID},
            "decision": "PASS",
        }
        for key, expected in exact.items():
            if proposed.get(key) != expected:
                raise ContractError("campaign approval does not match the exact PR10 request", {"field": key})
        approver = proposed.get("approver", {})
        if "PRIVATE_INTERNAL_VISUAL_TESTING" not in approver.get("authority", []):
            raise ContractError("campaign approver lacks private visual-testing authority")
        conditions = set(proposed.get("conditions", []))
        required_conditions = set(request_record["payload"]["conditions_required"])
        if not required_conditions.issubset(conditions):
            raise ContractError("campaign approval omits required fail-closed conditions")
        if proposed.get("maximum_paid_spend_minor_units") != 0:
            raise ContractError("PR10 campaign approval must retain the zero-spend cap")
        creator = proposed.get("creator", {"id": "autonomous-director"})
        approval = self.approvals.create(
            proposed["approval_type"], proposed["subject_type"], proposed["subject_hash"],
            proposed["scope"], approver, creator, proposed["decision"],
            inheritance_allowed=False, conditions=sorted(conditions),
            invalidators=["page_script_hash", "reference_hash", "backend_capability", "cost_policy"],
            evidence_refs=[plan_record["content_hash"], request_record["content_hash"]],
            source_scope="dm-source", tradition_id="devi-mahatmyam", edition_id="pargiter-1904",
            evidence_hash=plan["authorization_subject_hash"], expires_at=proposed.get("expires_at"),
        )
        status = self._status(plan_record, request_record)
        _write_if_changed(self.status_path, status)
        return {"status": status["status"], "approval": approval, "run": status, "mutated_art": False}

    def prepare_generation(self, page_id):
        plan_record, request_record = self._validate_stored()
        plan = plan_record["payload"]
        approval = self._approval(plan)
        if not approval:
            raise ContractError("PR10 generation is blocked pending exact campaign authorization", {
                "campaign_id": CAMPAIGN_ID,
                "subject_hash": plan["authorization_subject_hash"],
                "approval_request_record_hash": request_record["content_hash"],
            })
        pages = {item["page_id"]: item for item in plan["selected_pages"]}
        if page_id not in pages:
            raise ContractError("page is outside the authorized PR10 slice", {"page_id": page_id})
        page = pages[page_id]
        store = ImmutableVersionStore(self.books_root, "production-generation-requests/%s" % page_id)
        if len(store.versions(BOOK_ID)) >= page["operation_ceiling"]:
            raise ContractError("authorized PR10 per-page operation ceiling is exhausted", {"page_id": page_id})
        request = {
            "schema_version": "1.0",
            "campaign_id": CAMPAIGN_ID,
            "book_id": BOOK_ID,
            "page_id": page_id,
            "page_number": page["page_number"],
            "operation": page["operation"],
            "production_unit": page["delivery_mode"],
            "prompt": page["prompt"],
            "base_image": deepcopy(page["base_image"]),
            "references": deepcopy(page["references"]),
            "provider_id": plan["backend"]["provider_id"],
            "provider_interface": plan["backend"]["reference_input_interface"],
            "campaign_approval_id": approval["id"],
            "campaign_subject_hash": plan["authorization_subject_hash"],
            "page_script_sha256": page["page_script"]["sha256"],
            "lettering_hash": page["lettering_hash"],
            "text_in_image": False,
            "maximum_operations_for_page": 1,
            "maximum_paid_spend_minor_units": 0,
            "reference_conditioning_required": True,
        }
        request["request_hash"] = _unsigned_hash(request, "request_hash")
        record = store.put(BOOK_ID, request)
        return {"status": "READY_FOR_HOST_IMAGE_OPERATION", "request": request, "record": record, "mutated_art": False}

    def _generation_request_record(self, page_id):
        if page_id not in SELECTED_PAGE_IDS:
            raise ContractError("page is outside the authorized PR11 campaign", {"page_id": page_id})
        versions = self._store("production-generation-requests", page_id).versions(BOOK_ID)
        if len(versions) != 1:
            raise ContractError("PR11 image import requires exactly one prepared operation", {
                "page_id": page_id, "prepared_operations": len(versions),
            })
        record = versions[0]
        request = record["payload"]
        if request.get("request_hash") != _unsigned_hash(request, "request_hash"):
            raise ContractError("PR11 generation request hash is invalid")
        return record

    def import_image(self, page_id, request_path, image_path, provider_receipt_path):
        plan_record, request_record = self._validate_stored()
        plan = plan_record["payload"]
        if not self._approval(plan):
            raise ContractError("PR11 image import requires the exact campaign approval")
        generation_record = self._generation_request_record(page_id)
        supplied_request = load_json(Path(request_path))
        if supplied_request != generation_record:
            raise ContractError("PR11 image import does not bind the immutable prepared request")
        store = self._store("production-image-receipts", page_id)
        existing = store.versions(BOOK_ID)
        if existing:
            return {
                "status": existing[-1]["payload"]["status"],
                "record": existing[-1],
                "idempotent_replay": True,
                "run": self._status(plan_record, request_record),
            }
        if len(self._latest_by_page("production-image-receipts")) >= len(SELECTED_PAGE_IDS):
            raise ContractError("PR11 total two-operation ceiling is exhausted")
        request = generation_record["payload"]
        provider = load_json(Path(provider_receipt_path))
        exact = {
            "provider_id": request["provider_id"],
            "page_id": page_id,
            "operation": request["operation"],
            "request_hash": request["request_hash"],
            "campaign_subject_hash": plan["authorization_subject_hash"],
        }
        for key, expected in exact.items():
            if provider.get(key) != expected:
                raise ContractError("PR11 provider receipt does not bind the authorized operation", {"field": key})
        forbidden = {
            "api_key_supplied": provider.get("api_key_supplied"),
            "external_provider_authorization_requested": provider.get("external_provider_authorization_requested"),
            "paid_billing_requested": provider.get("paid_billing_requested"),
            "automatic_credit_purchase_requested": provider.get("automatic_credit_purchase_requested"),
        }
        if any(forbidden.values()):
            raise ContractError("PR11 receipt reports a forbidden billing or provider path", forbidden)
        if provider.get("purchased_credit_consumption") not in {"NOT_REQUESTED", "NOT_REPORTED_NO_BALANCE"}:
            raise ContractError("PR11 receipt does not preserve the purchased-credit prohibition")
        if provider.get("actual_incremental_usd") != "UNKNOWN_NOT_EXPOSED":
            raise ContractError("PR11 must not invent a zero-dollar result the tool did not expose")
        if provider.get("included_allowance_policy") != "CURRENT_INCLUDED_ALLOWANCE_FIRST":
            raise ContractError("PR11 receipt omits the approved allowance-first policy")
        reference_validation = validate_reference_receipt(request, provider)
        submitted = provider.get("submitted_references", [])
        first_reference_index = 1 + (1 if request["base_image"] else 0)
        expected_indexes = list(range(first_reference_index, first_reference_index + len(submitted)))
        if [item.get("input_index") for item in submitted] != expected_indexes:
            raise ContractError("PR11 submitted reference input order is not explicit and contiguous")
        edit_target = provider.get("submitted_edit_target")
        if request["base_image"]:
            expected_target = {
                "role": "EDIT_TARGET_REJECTED_PR6_SOURCE_ONLY",
                "path": request["base_image"]["path"],
                "sha256": request["base_image"]["sha256"],
                "input_index": 1,
            }
            if edit_target != expected_target:
                raise ContractError("PR11 edit receipt does not bind the exact rejected PR6 source")
        elif edit_target is not None:
            raise ContractError("PR11 generation receipt unexpectedly claims an edit target")
        prompt = provider.get("submitted_prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ContractError("PR11 provider receipt requires the exact submitted prompt")
        if provider.get("submitted_prompt_sha256") != sha256_bytes(prompt.encode("utf-8")):
            raise ContractError("PR11 submitted prompt hash is invalid")
        image_path = Path(image_path).resolve()
        try:
            relative_image = image_path.relative_to(self.root).as_posix()
        except ValueError as exc:
            raise ContractError("PR11 imported image must be preserved inside the repository") from exc
        expected_prefix = "books/DM04/production-pilot/images/%s/" % page_id
        if not relative_image.startswith(expected_prefix):
            raise ContractError("PR11 image is outside its page-specific pilot directory")
        image = inspect_png(image_path)
        if (image["width"], image["height"]) != (1086, 1448):
            raise ContractError("PR11 image does not match the locked 3:4 pixel canvas")
        if image["sha256"] != provider.get("output_sha256"):
            raise ContractError("PR11 provider receipt output hash does not match the actual pixels")
        payload = {
            "schema_version": "1.0",
            "milestone": "PR11",
            "book_id": BOOK_ID,
            "campaign_id": CAMPAIGN_ID,
            "campaign_subject_hash": plan["authorization_subject_hash"],
            "page_id": page_id,
            "operation": request["operation"],
            "generation_request_record_hash": generation_record["content_hash"],
            "request_hash": request["request_hash"],
            "provider": deepcopy(provider),
            "reference_validation": reference_validation,
            "image": dict(image, path=relative_image),
            "producer_ids": [provider["producer"]["id"]],
            "actual_cost_minor_units": None,
            "actual_cost_status": "UNKNOWN_TOOL_INTERFACE_DOES_NOT_EXPOSE_INCREMENTAL_USD",
            "status": "GENERATED_AWAITING_INDEPENDENT_VISUAL_REVIEW",
            "publication_eligible": False,
            "imported_at": utc_now(),
        }
        record = store.put(BOOK_ID, payload)
        status = self._status(plan_record, request_record)
        _write_if_changed(self.status_path, status)
        return {
            "status": payload["status"], "record": record, "image": payload["image"],
            "reference_validation": reference_validation, "idempotent_replay": False,
            "run": status,
        }

    def prepare_visual_review(self, page_id):
        plan_record, request_record = self._validate_stored()
        receipts = self._latest_by_page("production-image-receipts")
        if page_id not in receipts:
            raise ContractError("PR11 visual review requires imported real pixels", {"page_id": page_id})
        receipt = receipts[page_id]["payload"]
        store = self._store("production-visual-review-requests", page_id)
        existing = store.versions(BOOK_ID)
        if existing:
            record = existing[-1]
        else:
            request = {
                "schema_version": "1.0",
                "milestone": "PR11",
                "book_id": BOOK_ID,
                "campaign_subject_hash": plan_record["payload"]["authorization_subject_hash"],
                "page_id": page_id,
                "image_path": receipt["image"]["path"],
                "image_sha256": receipt["image"]["sha256"],
                "producer_ids": deepcopy(receipt["producer_ids"]),
                "comparison_references": deepcopy(receipt["provider"]["submitted_references"]),
                "required_dimensions": list(REVIEW_DIMENSIONS),
                "actual_pixels_required": True,
                "actual_reading_size_required": True,
                "independent_reviewer_required": True,
                "result_values": ["PASS", "FIX", "ESCALATE"],
            }
            request["request_hash"] = _unsigned_hash(request, "request_hash")
            record = store.put(BOOK_ID, request)
        status = self._status(plan_record, request_record)
        return {"status": "AWAITING_INDEPENDENT_ACTUAL_PIXEL_REVIEW", "record": record, "run": status}

    def import_visual_review(self, page_id, request_path, response_path):
        plan_record, campaign_request = self._validate_stored()
        requests = self._store("production-visual-review-requests", page_id).versions(BOOK_ID)
        if len(requests) != 1:
            raise ContractError("PR11 review import requires one immutable review request")
        supplied_request = load_json(Path(request_path))
        if supplied_request != requests[0]:
            raise ContractError("PR11 review response does not bind the immutable request record")
        request = requests[0]["payload"]
        response = load_json(Path(response_path))
        if response.get("request_hash") != request["request_hash"]:
            raise ContractError("PR11 visual review response request hash is stale")
        validation = validate_real_image_review(request, response)
        if response.get("overall_verdict") != validation["result"]:
            raise ContractError("PR11 review overall verdict conflicts with its dimension results")
        store = self._store("production-visual-reviews", page_id)
        existing = store.versions(BOOK_ID)
        payload = {
            "schema_version": "1.0",
            "milestone": "PR11",
            "book_id": BOOK_ID,
            "campaign_subject_hash": plan_record["payload"]["authorization_subject_hash"],
            "page_id": page_id,
            "request_record_hash": requests[0]["content_hash"],
            "request_hash": request["request_hash"],
            "image_path": request["image_path"],
            "image_sha256": request["image_sha256"],
            "reviewer": deepcopy(response["reviewer"]),
            "assessments": deepcopy(response["assessments"]),
            "findings": deepcopy(response.get("findings", [])),
            "correction_instructions": deepcopy(response.get("correction_instructions", [])),
            "preview_eligible": bool(response.get("preview_eligible")) and validation["result"] == "PASS",
            "result": validation["result"],
            "review_hash": validation["review_hash"],
            "independent_actual_pixel_review": True,
            "publication_eligible": False,
            "reviewed_at": utc_now(),
        }
        if existing:
            comparable = {key: value for key, value in payload.items() if key != "reviewed_at"}
            prior = {key: value for key, value in existing[-1]["payload"].items() if key != "reviewed_at"}
            if comparable != prior:
                raise ContractError("PR11 page already has a different immutable visual review")
            record = existing[-1]
        else:
            record = store.put(BOOK_ID, payload)
        correction_record = None
        if payload["result"] != "PASS":
            correction_store = self._store("production-correction-requests", page_id)
            corrections = correction_store.versions(BOOK_ID)
            correction = {
                "schema_version": "1.0",
                "milestone": "PR11",
                "book_id": BOOK_ID,
                "page_id": page_id,
                "failed_image_sha256": request["image_sha256"],
                "visual_review_hash": validation["review_hash"],
                "result": payload["result"],
                "localized_findings": deepcopy(payload["findings"]),
                "targeted_correction_instructions": deepcopy(payload["correction_instructions"]),
                "generation_retry_authorized": False,
                "remaining_campaign_image_operations": 0,
                "pr6_counter_reset": False,
                "preserve_other_page": True,
                "publication_eligible": False,
            }
            if corrections:
                if corrections[-1]["payload"] != correction:
                    raise ContractError("PR11 correction request already differs")
                correction_record = corrections[-1]
            else:
                correction_record = correction_store.put(BOOK_ID, correction)
        status = self._status(plan_record, campaign_request)
        _write_if_changed(self.status_path, status)
        return {
            "status": status["status"], "review": record,
            "correction_request": correction_record, "run": status,
        }

    def validate(self):
        plan_record, request_record = self._validate_stored()
        status = self._status(plan_record, request_record)
        recovery_fixture = load_json(self.root / "book-factory" / "fixtures" / "real-production-integration" / "page-local-recovery.json")
        if recovery_fixture.get("fixture") is not True or recovery_fixture.get("publication_eligible") is not False:
            raise ContractError("PR10 recovery demonstration is not isolated")
        route = route_page_repair(recovery_fixture["finding"])
        if route["invalidate_scope"] != "PAGE_LOCAL" or not route["preserve_other_pages"] or route["reset_retry_counter"]:
            raise ContractError("PR10 isolated recovery did not preserve unaffected pages and attempt history")
        if status["actual_image_operations"] > 2:
            raise ContractError("PR11 campaign exceeded its two-operation ceiling")
        if status["actual_image_operations"] and status["actual_cost_status"] != "UNKNOWN_TOOL_INTERFACE_DOES_NOT_EXPOSE_INCREMENTAL_USD":
            raise ContractError("PR11 must preserve the unknown direct-cost observation")
        return {
            "status": "PASS",
            "plan_hash": plan_record["content_hash"],
            "approval_request_hash": request_record["content_hash"],
            "selected_page_ids": list(SELECTED_PAGE_IDS),
            "generation_authorized": status["generation_authorized"],
            "actual_image_operations": status["actual_image_operations"],
            "actual_cost_minor_units": status["actual_cost_minor_units"],
            "isolated_recovery": route,
            "publication_eligible": False,
        }
