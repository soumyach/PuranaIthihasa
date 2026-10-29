"""PR12 bounded autonomous multi-page pilot controls.

The Director persists an exact five-operation DM04 campaign, imports the
current-session human authorization, prepares host-only image requests, and
binds returned pixels and independent reviews.  It never invokes a paid API,
resets an older retry counter, or turns a private preview into publication
approval.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from .approvals import ApprovalStore
from .errors import ContractError
from .illustration_production import inspect_png
from .production_integration import REVIEW_DIMENSIONS, validate_real_image_review
from .util import atomic_json_write, content_hash, load_json, sha256_bytes, utc_now
from .versioning import ImmutableVersionStore


BOOK_ID = "DM04"
CAMPAIGN_ID = "dm04-pr12-autonomous-multi-page-pilot-01"
MAXIMUM_OPERATIONS = 5

UNITS = (
    {
        "unit_id": "page-27d143ae995bf60742b65c5b--p01-panel-02",
        "page_id": "page-27d143ae995bf60742b65c5b",
        "page_number": 1,
        "panel_id": "p01-panel-02",
        "page_script": "books/DM04/page-scripts/page-0001.v0003.json",
        "operation": "edit",
        "selection_role": "INTIMATE_CONVERSATION",
        "base_image": "books/DM04/production-pilot/images/page-27d143ae995bf60742b65c5b/v0001.png",
        "reference_a": "kgs-satya-p01",
        "reference_b": "kgs-dm08-p09",
        "prompt": (
            "Create one clean landscape comic-panel illustration for DM04 page 1 panel 2. "
            "EDIT TARGET: preserve the exact three established people, clothing, dusk forest-hermitage, "
            "firelight and painterly finish from the supplied DM04 image, but change the camera to a genuine "
            "intimate over-shoulder view from behind both listeners: Suratha's muted-blue royal shoulder at "
            "left foreground and Samadhi's plain earth-toned shoulder at right foreground, both facing Sage "
            "Medhas. Medhas is the clearly readable speaking focus, aged, white-bearded, seated and gesturing "
            "calmly across the low fire. Their attentive silence must read in posture. Reserve uncluttered upper "
            "branches and lower-left space for later editable lettering. REFERENCE A supplies only Khatakshetra "
            "premium devotional painterly identity and navy-gold sensibility. REFERENCE B supplies only intimate "
            "speaker-listener staging and clear reaction-driven comic storytelling. Do not transfer any deity, "
            "lion, architecture, clothing identity or story content from the references. No embedded text, "
            "balloons, border, watermark, modern objects, Western fantasy armor, helmets or emblems. Family-reading "
            "appropriate. One moment only; no duplicated figures."
        ),
    },
    {
        "unit_id": "page-23e0e9cd9d4013ed03ae7e8c--p13-panel-01",
        "page_id": "page-23e0e9cd9d4013ed03ae7e8c",
        "page_number": 13,
        "panel_id": "p13-panel-01",
        "page_script": "books/DM04/page-scripts/page-0013.v0003.json",
        "operation": "generate",
        "selection_role": "ACTION_MISSILE_COUNTER",
        "base_image": None,
        "reference_a": "kgs-satya-p01",
        "reference_b": "kgs-dm08-p21",
        "prompt": (
            "Create one clean landscape comic-panel illustration for DM04 page 13 panel 1, a skyward diagonal "
            "battle action. Devī/Chandikā is the serene authoritative focal defender in classical modest Indian "
            "dress, deep blue, warm ivory and antique gold, with a radiant crown. Show a readable many-armed "
            "identity only through the foreground arms needed for this exact action plus a restrained implied arm "
            "field; do not invent weapons. Arrows, spears and heavy weapons fly diagonally toward her from the "
            "asura ranks; she cuts them apart before impact, with broken shafts falling in front of—not through—the "
            "first ranks. Keep trajectories and cause-effect unmistakable, energetic but non-graphic. The battlefield "
            "has a stable distant ridge, hard daylight and an uncluttered upper-left lettering zone. REFERENCE A "
            "supplies only premium Khatakshetra devotional painterly finish. REFERENCE B supplies only large-scale "
            "battle depth and sequential action clarity; omit its blood, flags, armor, characters and theology. "
            "No text, balloons, border, watermark, gore, Western fantasy armor, Greco-Roman helmets, invented "
            "emblems, demonic-face flags or unrelated divine iconography. Family-reading appropriate."
        ),
    },
    {
        "unit_id": "page-23e0e9cd9d4013ed03ae7e8c--p13-panel-02",
        "page_id": "page-23e0e9cd9d4013ed03ae7e8c",
        "page_number": 13,
        "panel_id": "p13-panel-02",
        "page_script": "books/DM04/page-scripts/page-0013.v0003.json",
        "operation": "generate",
        "selection_role": "ACTION_GROUND_COUNTER",
        "base_image": None,
        "reference_a": "kgs-satya-p01",
        "reference_b": "kgs-dm08-p21",
        "prompt": (
            "Create one clean landscape comic-panel illustration for DM04 page 13 panel 2, a distinct ground-level "
            "counterframe after the missile exchange. Devī/Chandikā keeps the same serene authoritative visual "
            "design: classical modest Indian dress in deep blue, warm ivory and antique gold, radiant crown, "
            "readable many-armed identity with only sourced equipment. Her tawny-gold lion with dark mane splits "
            "the asura soldiers' formation. Devī's Varuṇa-given noose visibly catches the nearest attackers while "
            "her other sourced weapons hold the center; show one visible breath beginning as the transition toward "
            "the next page, without yet depicting the breath-born army. Use a low camera, clear action lanes, stable "
            "distant ridge, charcoal/oxblood enemy massing, and an uncluttered top zone for later narration. "
            "REFERENCE A supplies only premium Khatakshetra devotional painterly finish. REFERENCE B supplies only "
            "battle depth and readable sequential action; omit its blood, flags, armor, characters and theology. "
            "No text, balloons, border, watermark, gore, Western fantasy armor, Greco-Roman helmets, invented "
            "emblems, demonic-face flags or unrelated iconography. Family-reading appropriate."
        ),
    },
    {
        "unit_id": "page-5aca23381e148b472373cd8c--p14-panel-01",
        "page_id": "page-5aca23381e148b472373cd8c",
        "page_number": 14,
        "panel_id": "p14-panel-01",
        "page_script": "books/DM04/page-scripts/page-0014.v0003.json",
        "operation": "generate",
        "selection_role": "DRAMATIC_REVELATION_IMMERSIVE",
        "base_image": None,
        "reference_a": "kgs-satya-p01",
        "reference_b": "kgs-dm08-p12",
        "prompt": (
            "Create one clean portrait 3:4 immersive full-page illustration for DM04 page 14. Devī/Chandikā is at "
            "the top center, serene and commanding in classical modest Indian dress, deep blue, warm ivory and "
            "antique gold, radiant crown, readable many-armed identity using sourced equipment only. A luminous "
            "battle breath visibly leaves her and resolves in layered stages into disciplined warm ivory-gold "
            "troops below, carrying exactly axes, javelins, swords and halberds. Drums and conches answer; subtle "
            "concentric bell waves confound the charcoal-and-oxblood asura formation along the lower edge as it "
            "breaks before the advance. Make emergence, instruments and consequence legible without compressing "
            "unrelated actions. Preserve a stable distant ridge and a calm upper-left parchment-safe area. "
            "REFERENCE A supplies premium Khatakshetra devotional painterly identity and focal hierarchy. REFERENCE "
            "B supplies only transformation sequencing, battlefield depth and cinematic reveal; do not transfer "
            "Kali/Chamunda, skulls, blood, flags, opponents, weapons or theology. No text, balloons, border, watermark, "
            "gore, Western fantasy armor, Greco-Roman helmets, invented emblems or unrelated divine iconography. "
            "Family-reading appropriate."
        ),
    },
    {
        "unit_id": "page-54d61ef5bfcb1159088ac489--p23-panel-01",
        "page_id": "page-54d61ef5bfcb1159088ac489",
        "page_number": 23,
        "panel_id": "p23-panel-01",
        "page_script": "books/DM04/page-scripts/page-0023.v0003.json",
        "operation": "generate",
        "selection_role": "ACTION_IMMERSIVE_REVERSAL",
        "base_image": None,
        "reference_a": "kgs-satya-p01",
        "reference_b": "kgs-dm08-p28",
        "prompt": (
            "Create one clean portrait 3:4 immersive full-page illustration for DM04 page 23, a single exact "
            "reversal. Mahiṣāsura appears only in massive dark-umber buffalo form, surging from the near foreground; "
            "his muzzle, hooves, tail and horns scatter the warm ivory-gold breath-born troops. Do not show a human, "
            "lion or elephant antagonist form. At the top of the vertical field, Devī/Chandikā and her distinct "
            "tawny-gold dark-maned lion hold a small but unbroken opposing line. Devī wears classical modest Indian "
            "dress in deep blue, warm ivory and antique gold, with radiant crown and sourced equipment only. Use "
            "storm-dark edge light against her gold, readable depth, stable ridge and an uncluttered upper-left "
            "lettering area. REFERENCE A supplies premium Khatakshetra devotional painterly identity and focal "
            "hierarchy. REFERENCE B supplies only immersive climax depth and before/after visual force; omit its "
            "characters, blood, flags, skulls, armor, weapons and theology. No text, balloons, border, watermark, "
            "gore, Western fantasy armor, Greco-Roman helmets, invented emblems or unrelated divine iconography. "
            "Family-reading appropriate."
        ),
    },
)


def _unsigned_hash(record, hash_field):
    return content_hash({key: value for key, value in record.items() if key != hash_field})


def _write_if_changed(path, value):
    path = Path(path)
    if path.is_file() and load_json(path) == value:
        return False
    atomic_json_write(path, value)
    return True


class AutonomousMultiPagePilot:
    """Exact PR12 campaign boundary used by the existing Director facade."""

    def __init__(self, repository_root):
        self.root = Path(repository_root).resolve()
        self.books_root = self.root / "books"
        self.book_root = self.books_root / BOOK_ID
        self.slice_store = ImmutableVersionStore(self.books_root, "production-slices")
        self.request_store = ImmutableVersionStore(self.books_root, "production-campaign-requests")
        self.approvals = ApprovalStore(self.book_root / "approvals")
        self.status_path = self.book_root / "autonomous-pilot-status.json"

    def _store(self, kind, unit_id):
        return ImmutableVersionStore(self.books_root, "%s/%s" % (kind, unit_id))

    def _asset(self, relative_path, role=None):
        path = self.root / relative_path
        if not path.is_file():
            raise ContractError("required PR12 input is missing", {"path": relative_path})
        asset = {"path": relative_path, "sha256": sha256_bytes(path.read_bytes()), "bytes": path.stat().st_size}
        if role:
            asset["role"] = role
        return asset

    def _reference(self, reference_id, role):
        manifest = load_json(self.root / "book-factory/references/visual-gold-standard/manifest.json")
        matches = [item for item in manifest["pages"] if item["reference_id"] == reference_id]
        if len(matches) != 1:
            raise ContractError("PR12 visual reference is not uniquely registered", {"reference_id": reference_id})
        item = matches[0]
        asset = self._asset(item["extracted_path"])
        if asset["sha256"] != item["extracted_sha256"]:
            raise ContractError("PR12 visual reference hash changed", {"reference_id": reference_id})
        return {
            "role": role,
            "reference_id": reference_id,
            "path": item["extracted_path"],
            "sha256": asset["sha256"],
            "available": True,
            "approval_status": "CURATED_PRESENTATION_REFERENCE_NOT_SOURCE_AUTHORITY",
            "content_transfer": "FORBIDDEN",
        }

    def _unit(self, spec):
        page = load_json(self.root / spec["page_script"])
        if page.get("page_id") != spec["page_id"] or page.get("page_number") != spec["page_number"]:
            raise ContractError("PR12 selected page identity changed", {"unit_id": spec["unit_id"]})
        panel = next((item for item in page.get("panels", []) if item.get("id") == spec["panel_id"]), None)
        if panel is None:
            raise ContractError("PR12 selected panel is missing", {"unit_id": spec["unit_id"]})
        references = [
            self._reference(spec["reference_a"], "A_SERIES_VISUAL_IDENTITY"),
            self._reference(spec["reference_b"], "B_PAGE_PANEL_COMPOSITION"),
            {
                "role": "C_APPROVED_CHARACTER_REFERENCE",
                "available": False,
                "approval_status": "UNAVAILABLE_NO_HUMAN_APPROVED_EXACT_DM04_CHARACTER_ASSET",
                "content_transfer": "NOT_APPLICABLE",
            },
            {
                "role": "D_APPROVED_SETTING_REFERENCE",
                "available": False,
                "approval_status": "UNAVAILABLE_NO_HUMAN_APPROVED_EXACT_DM04_SETTING_ASSET",
                "content_transfer": "NOT_APPLICABLE",
            },
        ]
        base = self._asset(spec["base_image"], "EDIT_TARGET_EXISTING_FIX_ART_REFERENCE_ONLY") if spec["base_image"] else None
        return {
            "unit_id": spec["unit_id"],
            "page_id": spec["page_id"],
            "page_number": spec["page_number"],
            "page_title": page["title"],
            "panel_id": spec["panel_id"],
            "panel_count": page["panel_count"],
            "selection_role": spec["selection_role"],
            "operation": spec["operation"],
            "operation_ceiling": 1,
            "page_script": self._asset(spec["page_script"], "LOCKED_PAGE_SCRIPT"),
            "event_ids": deepcopy(page["event_ids"]),
            "source_claim_ids": deepcopy(page["source_claim_ids"]),
            "character_ids": deepcopy(panel["character_ids"]),
            "location_id": panel["location_id"],
            "locked_action": panel["visual_description"],
            "lettering": deepcopy(page["lettering"]),
            "lettering_hash": content_hash(page["lettering"]),
            "base_image": base,
            "references": references,
            "reference_package_hash": content_hash(references),
            "prompt": spec["prompt"],
            "prompt_sha256": sha256_bytes(spec["prompt"].encode("utf-8")),
            "text_in_image": False,
        }

    def _build_plan(self):
        units = [self._unit(spec) for spec in UNITS]
        production_status = load_json(self.book_root / "production-status.json")
        pr11_status = load_json(self.book_root / "production-integration-status.json")
        locked_inputs = [
            self._asset("MYTHOLOGY_COMIC_RULES.md", "SERIES_RULES"),
            self._asset("books/DM04/manuscripts/v0005.json", "MANUSCRIPT_V5"),
            self._asset("books/DM04/storyboards/v0003.json", "STORYBOARD_V3"),
            self._asset("books/DM04/character-bibles/v0004.json", "CHARACTER_BIBLE"),
            self._asset("books/DM04/location-bibles/v0002.json", "LOCATION_BIBLE"),
            self._asset("books/DM04/source-readiness/75a6d7223209feb8850b482d9e0876cd323991652b436ac139470cadc95041d3.json", "SOURCE_DOSSIER"),
            self._asset("books/DM04/story-packets/b784b365d9c921312285f453b4f6a4a15a7be935e2f0fdda6cfa8eba12797744.json", "STORY_PACKET"),
            self._asset("book-factory/references/visual-gold-standard/manifest.json", "VISUAL_GOLD_STANDARD"),
            self._asset("books/DM04/production-status.json", "PR6_STATUS"),
            self._asset("books/DM04/production-integration-status.json", "PR11_STATUS"),
        ]
        subject = {
            "campaign_id": CAMPAIGN_ID,
            "book_id": BOOK_ID,
            "purpose": "PRIVATE_INTERNAL_AUTONOMOUS_MULTI_PAGE_PRODUCTION_PILOT",
            "unit_ids": [unit["unit_id"] for unit in units],
            "operations": [unit["operation"] for unit in units],
            "operation_ceiling_total": MAXIMUM_OPERATIONS,
            "operation_ceiling_per_unit": 1,
            "maximum_paid_spend_minor_units": 0,
            "currency": "USD",
            "provider_id": "codex-built-in-image-gen",
            "included_allowance_first": True,
            "purchased_credits_authorized": False,
            "api_or_external_provider_authorized": False,
            "publication_authorized": False,
            "pr6_counter_reset": False,
            "pr11_counter_reset": False,
            "unit_prompt_hashes": [unit["prompt_sha256"] for unit in units],
            "unit_reference_hashes": [unit["reference_package_hash"] for unit in units],
            "locked_input_sha256": sorted(asset["sha256"] for asset in locked_inputs),
        }
        return {
            "schema_version": "1.0",
            "milestone": "PR12",
            "book_id": BOOK_ID,
            "campaign_id": CAMPAIGN_ID,
            "purpose": subject["purpose"],
            "authorization_subject": subject,
            "authorization_subject_hash": content_hash(subject),
            "units": units,
            "locked_inputs": locked_inputs,
            "backend": {
                "provider_id": "codex-built-in-image-gen",
                "host_tool": "image_gen.imagegen",
                "reference_input_interface": "referenced_image_paths",
                "repository_programmatic_invocation": False,
            },
            "cost_policy": {
                "included_allowance_first": True,
                "maximum_paid_spend_minor_units": 0,
                "purchased_credit_consumption_authorized": False,
                "external_provider_authorized": False,
                "actual_incremental_usd_exposed_by_tool": False,
            },
            "preservation": {
                "pr6_real_images_generated_total_before": production_status.get("real_images_generated_total"),
                "pr6_exact_result_before": production_status.get("exact_result"),
                "pr6_proof_image_hashes_before": deepcopy(production_status.get("proof_image_hashes", [])),
                "pr11_campaign_id": pr11_status.get("campaign_id"),
                "pr11_operations_before": pr11_status.get("actual_image_operations"),
                "source_graph_mutation_authorized": False,
                "dm08_mutation_authorized": False,
            },
            "publication_eligible": False,
        }

    def _approval_request(self, plan_record):
        plan = plan_record["payload"]
        request = {
            "schema_version": "1.0",
            "milestone": "PR12",
            "request_type": "PRODUCTION_CAMPAIGN_AUTHORIZATION",
            "approval_type": "PRODUCTION_CAMPAIGN",
            "book_id": BOOK_ID,
            "campaign_id": CAMPAIGN_ID,
            "subject_type": "PRODUCTION_CAMPAIGN",
            "subject_hash": plan["authorization_subject_hash"],
            "scope": {"type": "book", "id": BOOK_ID},
            "plan_record_hash": plan_record["content_hash"],
            "requested_authority": "PRIVATE_INTERNAL_VISUAL_TESTING_ONLY",
            "requested_units": [
                {"unit_id": unit["unit_id"], "page_id": unit["page_id"], "panel_id": unit["panel_id"], "operation": unit["operation"], "maximum_operations": 1}
                for unit in plan["units"]
            ],
            "conditions_required": [
                "PRIVATE_INTERNAL_ONLY",
                "PUBLICATION_REMAINS_BLOCKED",
                "BUILT_IN_CODEX_IMAGE_TOOL_ONLY",
                "INCLUDED_ALLOWANCE_FIRST",
                "NO_SEPARATELY_BILLED_API_OR_EXTERNAL_PROVIDER",
                "NO_PURCHASED_CREDIT_CONSUMPTION_INTENDED",
                "FIVE_OPERATIONS_TOTAL_CEILING",
                "ONE_OPERATION_PER_UNIT_NO_AUTOMATIC_RETRY",
                "PR6_AND_PR11_COUNTERS_UNCHANGED",
                "EXACT_REFERENCE_RECEIPTS_REQUIRED",
                "INDEPENDENT_ACTUAL_PIXEL_REVIEW_REQUIRED",
            ],
            "maximum_paid_spend_minor_units": 0,
            "currency": "USD",
            "approval_not_implied_by_request": True,
        }
        request["request_hash"] = _unsigned_hash(request, "request_hash")
        return request

    def _latest_records(self, kind):
        result = {}
        for spec in UNITS:
            versions = self._store(kind, spec["unit_id"]).versions(BOOK_ID)
            if len(versions) > 1:
                raise ContractError("PR12 one-operation-per-unit ceiling exceeded", {"kind": kind, "unit_id": spec["unit_id"]})
            if versions:
                result[spec["unit_id"]] = versions[-1]
        return result

    def _approval(self, plan):
        return self.approvals.find_valid(
            "PRODUCTION_CAMPAIGN", plan["authorization_subject_hash"], {"type": "book", "id": BOOK_ID},
            target_context={"source_scope": "dm-source", "tradition_id": "devi-mahatmyam", "edition_id": "pargiter-1904"},
            current_evidence_hash=plan["authorization_subject_hash"],
        )

    def _validate_stored(self):
        plans = self.slice_store.versions(BOOK_ID)
        requests = self.request_store.versions(BOOK_ID)
        if len(plans) < 2 or len(requests) < 2:
            raise ContractError("PR12 campaign has not been prepared")
        expected_plan = self._build_plan()
        matching_plans = [record for record in plans if record["payload"] == expected_plan]
        if not matching_plans:
            raise ContractError("stored PR12 production slice is stale")
        plan_record = matching_plans[-1]
        expected_request = self._approval_request(plan_record)
        matching_requests = [record for record in requests if record["payload"] == expected_request]
        if not matching_requests:
            raise ContractError("stored PR12 campaign request is stale")
        request_record = matching_requests[-1]
        return plan_record, request_record

    def _status(self, plan_record, request_record):
        plan = plan_record["payload"]
        approval = self._approval(plan)
        images = self._latest_records("autonomous-pilot-image-receipts")
        reviews = self._latest_records("autonomous-pilot-visual-reviews")
        if not approval:
            lifecycle = "AWAITING_CAMPAIGN_AUTHORIZATION"
        elif len(images) < MAXIMUM_OPERATIONS:
            lifecycle = "AUTHORIZED_AWAITING_IMAGE_OPERATIONS"
        elif len(reviews) < len(images):
            lifecycle = "GENERATED_AWAITING_INDEPENDENT_VISUAL_REVIEW"
        elif all(record["payload"]["result"] == "PASS" for record in reviews.values()):
            lifecycle = "REVIEWED_PASS_PRIVATE_COMPOSITION_ELIGIBLE"
        else:
            lifecycle = "REVIEWED_WITH_BLOCKERS_CAMPAIGN_COMPLETE_NO_RETRY"
        status = {
            "schema_version": "1.0",
            "milestone": "PR12",
            "book_id": BOOK_ID,
            "campaign_id": CAMPAIGN_ID,
            "status": lifecycle,
            "campaign_subject_hash": plan["authorization_subject_hash"],
            "approval_request_record_hash": request_record["content_hash"],
            "approval_id": approval.get("id") if approval else None,
            "generation_authorized": bool(approval),
            "operation_ceiling": MAXIMUM_OPERATIONS,
            "image_operations_executed": len(images),
            "remaining_image_operations": MAXIMUM_OPERATIONS - len(images),
            "independent_reviews_completed": len(reviews),
            "review_results": {key: value["payload"]["result"] for key, value in reviews.items()},
            "actual_incremental_usd": "UNKNOWN_NOT_EXPOSED" if images else "NOT_APPLICABLE_NO_OPERATION",
            "separately_billed_provider_calls": 0,
            "purchased_credit_consumption": "NOT_REQUESTED_OR_REPORTED",
            "publication_eligible": False,
            "pr6_counter_reset": False,
            "pr11_counter_reset": False,
        }
        status["status_hash"] = _unsigned_hash(status, "status_hash")
        return status

    def prepare(self):
        plans = self.slice_store.versions(BOOK_ID)
        requests = self.request_store.versions(BOOK_ID)
        plan = self._build_plan()
        matching_plans = [record for record in plans if record["payload"] == plan]
        plan_record = matching_plans[-1] if matching_plans else self.slice_store.put(
            BOOK_ID, plan, plans[-1]["content_hash"] if plans else None,
        )
        request = self._approval_request(plan_record)
        matching_requests = [record for record in requests if record["payload"] == request]
        request_record = matching_requests[-1] if matching_requests else self.request_store.put(
            BOOK_ID, request, requests[-1]["content_hash"] if requests else None,
        )
        status = self._status(plan_record, request_record)
        _write_if_changed(self.status_path, status)
        return {"status": status["status"], "plan": plan_record, "approval_request": request_record, "run": status}

    def import_approval(self, approval_path):
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
                raise ContractError("PR12 approval does not match the exact campaign", {"field": key})
        approver = proposed.get("approver", {})
        if "PRIVATE_INTERNAL_VISUAL_TESTING" not in approver.get("authority", []):
            raise ContractError("PR12 approver lacks private visual-testing authority")
        conditions = set(proposed.get("conditions", []))
        required = set(request_record["payload"]["conditions_required"])
        if not required.issubset(conditions):
            raise ContractError("PR12 approval omits required fail-closed conditions")
        if proposed.get("maximum_paid_spend_minor_units") != 0:
            raise ContractError("PR12 approval must retain the zero-spend authorization cap")
        approval = self.approvals.create(
            proposed["approval_type"], proposed["subject_type"], proposed["subject_hash"], proposed["scope"],
            approver, proposed.get("creator", {"id": "autonomous-director-pr12"}), proposed["decision"],
            inheritance_allowed=False, conditions=sorted(conditions),
            invalidators=["unit_prompt_hash", "reference_hash", "provider", "cost_policy"],
            evidence_refs=[plan_record["content_hash"], request_record["content_hash"], "CURRENT_USER_MESSAGE_PR12"],
            source_scope="dm-source", tradition_id="devi-mahatmyam", edition_id="pargiter-1904",
            evidence_hash=plan["authorization_subject_hash"], expires_at=proposed.get("expires_at"),
        )
        status = self._status(plan_record, request_record)
        _write_if_changed(self.status_path, status)
        return {"status": status["status"], "approval": approval, "run": status}

    def prepare_generation(self, unit_id):
        plan_record, request_record = self._validate_stored()
        plan = plan_record["payload"]
        approval = self._approval(plan)
        if not approval:
            raise ContractError("PR12 generation requires the exact campaign approval")
        units = {unit["unit_id"]: unit for unit in plan["units"]}
        if unit_id not in units:
            raise ContractError("unit is outside the authorized PR12 campaign", {"unit_id": unit_id})
        if len(self._latest_records("autonomous-pilot-image-receipts")) >= MAXIMUM_OPERATIONS:
            raise ContractError("PR12 five-operation ceiling is exhausted")
        store = self._store("autonomous-pilot-generation-requests", unit_id)
        if store.versions(BOOK_ID):
            raise ContractError("PR12 unit already has a prepared one-shot operation", {"unit_id": unit_id})
        unit = units[unit_id]
        request = {
            "schema_version": "1.0",
            "milestone": "PR12",
            "campaign_id": CAMPAIGN_ID,
            "campaign_subject_hash": plan["authorization_subject_hash"],
            "campaign_approval_id": approval["id"],
            "book_id": BOOK_ID,
            "unit_id": unit_id,
            "page_id": unit["page_id"],
            "panel_id": unit["panel_id"],
            "operation": unit["operation"],
            "prompt": unit["prompt"],
            "prompt_sha256": unit["prompt_sha256"],
            "base_image": deepcopy(unit["base_image"]),
            "references": deepcopy(unit["references"]),
            "provider_id": "codex-built-in-image-gen",
            "provider_interface": "referenced_image_paths",
            "text_in_image": False,
            "maximum_operations_for_unit": 1,
            "maximum_paid_spend_minor_units": 0,
            "automatic_retry_authorized": False,
        }
        request["request_hash"] = _unsigned_hash(request, "request_hash")
        record = store.put(BOOK_ID, request)
        return {"status": "READY_FOR_ONE_HOST_IMAGE_OPERATION", "record": record, "request": request}

    def import_image(self, unit_id, request_path, image_path, provider_receipt_path):
        plan_record, request_record = self._validate_stored()
        if not self._approval(plan_record["payload"]):
            raise ContractError("PR12 image import requires the exact campaign approval")
        requests = self._store("autonomous-pilot-generation-requests", unit_id).versions(BOOK_ID)
        if len(requests) != 1 or load_json(Path(request_path)) != requests[0]:
            raise ContractError("PR12 image import does not bind its immutable prepared request")
        store = self._store("autonomous-pilot-image-receipts", unit_id)
        if store.versions(BOOK_ID):
            return {"status": "IDEMPOTENT_REPLAY", "record": store.versions(BOOK_ID)[0]}
        if len(self._latest_records("autonomous-pilot-image-receipts")) >= MAXIMUM_OPERATIONS:
            raise ContractError("PR12 five-operation ceiling is exhausted")
        request = requests[0]["payload"]
        provider = load_json(Path(provider_receipt_path))
        for key, expected in {
            "provider_id": request["provider_id"],
            "unit_id": unit_id,
            "operation": request["operation"],
            "request_hash": request["request_hash"],
            "campaign_subject_hash": plan_record["payload"]["authorization_subject_hash"],
        }.items():
            if provider.get(key) != expected:
                raise ContractError("PR12 provider receipt does not bind the authorized operation", {"field": key})
        if any(provider.get(field) for field in (
            "api_key_supplied", "external_provider_authorization_requested", "paid_billing_requested", "automatic_credit_purchase_requested"
        )):
            raise ContractError("PR12 receipt reports a forbidden billing or provider path")
        if provider.get("purchased_credit_consumption") not in {"NOT_REQUESTED", "NOT_REPORTED_NO_BALANCE"}:
            raise ContractError("PR12 receipt violates purchased-credit policy")
        if provider.get("actual_incremental_usd") != "UNKNOWN_NOT_EXPOSED":
            raise ContractError("PR12 must not invent a zero-dollar result")
        if provider.get("included_allowance_policy") != "CURRENT_INCLUDED_ALLOWANCE_FIRST":
            raise ContractError("PR12 receipt omits included-allowance-first policy")
        if provider.get("submitted_prompt") != request["prompt"] or provider.get("submitted_prompt_sha256") != request["prompt_sha256"]:
            raise ContractError("PR12 receipt does not preserve the exact submitted prompt")
        expected_refs = [item for item in request["references"] if item.get("available")]
        submitted_refs = provider.get("submitted_references", [])
        if [{key: item.get(key) for key in ("role", "path", "sha256")} for item in submitted_refs] != [
            {key: item.get(key) for key in ("role", "path", "sha256")} for item in expected_refs
        ]:
            raise ContractError("PR12 reference receipt differs from the authorized A/B inputs")
        image_path = Path(image_path).resolve()
        try:
            relative = image_path.relative_to(self.root).as_posix()
        except ValueError as exc:
            raise ContractError("PR12 image must be preserved inside the repository") from exc
        expected_prefix = "books/DM04/autonomous-pilot/images/%s/" % unit_id
        if not relative.startswith(expected_prefix):
            raise ContractError("PR12 image is outside its unit-specific directory")
        image = inspect_png(image_path)
        if image["sha256"] != provider.get("output_sha256"):
            raise ContractError("PR12 receipt output hash does not match actual pixels")
        payload = {
            "schema_version": "1.0",
            "milestone": "PR12",
            "book_id": BOOK_ID,
            "campaign_id": CAMPAIGN_ID,
            "campaign_subject_hash": plan_record["payload"]["authorization_subject_hash"],
            "unit_id": unit_id,
            "page_id": request["page_id"],
            "panel_id": request["panel_id"],
            "operation": request["operation"],
            "generation_request_record_hash": requests[0]["content_hash"],
            "request_hash": request["request_hash"],
            "provider": deepcopy(provider),
            "image": dict(image, path=relative),
            "producer_ids": [provider["producer"]["id"]],
            "status": "GENERATED_AWAITING_INDEPENDENT_VISUAL_REVIEW",
            "publication_eligible": False,
            "imported_at": utc_now(),
        }
        record = store.put(BOOK_ID, payload)
        status = self._status(plan_record, request_record)
        _write_if_changed(self.status_path, status)
        return {"status": payload["status"], "record": record, "image": payload["image"], "run": status}

    def prepare_visual_review(self, unit_id):
        plan_record, request_record = self._validate_stored()
        receipts = self._latest_records("autonomous-pilot-image-receipts")
        if unit_id not in receipts:
            raise ContractError("PR12 review requires imported real pixels", {"unit_id": unit_id})
        receipt = receipts[unit_id]["payload"]
        store = self._store("autonomous-pilot-visual-review-requests", unit_id)
        if store.versions(BOOK_ID):
            record = store.versions(BOOK_ID)[0]
        else:
            request = {
                "schema_version": "1.0",
                "milestone": "PR12",
                "campaign_subject_hash": plan_record["payload"]["authorization_subject_hash"],
                "unit_id": unit_id,
                "page_id": receipt["page_id"],
                "panel_id": receipt["panel_id"],
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
        return {"status": "AWAITING_INDEPENDENT_ACTUAL_PIXEL_REVIEW", "record": record, "run": self._status(plan_record, request_record)}

    def import_visual_review(self, unit_id, request_path, response_path):
        plan_record, request_record = self._validate_stored()
        requests = self._store("autonomous-pilot-visual-review-requests", unit_id).versions(BOOK_ID)
        if len(requests) != 1 or load_json(Path(request_path)) != requests[0]:
            raise ContractError("PR12 review response does not bind its immutable request")
        request = requests[0]["payload"]
        response = load_json(Path(response_path))
        if response.get("request_hash") != request["request_hash"] or response.get("unit_id") != unit_id:
            raise ContractError("PR12 visual review response is stale or targets another unit")
        validation = validate_real_image_review(request, response)
        if response.get("overall_verdict") != validation["result"]:
            raise ContractError("PR12 review verdict conflicts with dimension results")
        payload = {
            "schema_version": "1.0",
            "milestone": "PR12",
            "book_id": BOOK_ID,
            "campaign_subject_hash": plan_record["payload"]["authorization_subject_hash"],
            "unit_id": unit_id,
            "page_id": request["page_id"],
            "panel_id": request["panel_id"],
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
            "generation_retry_authorized": False,
            "reviewed_at": utc_now(),
        }
        store = self._store("autonomous-pilot-visual-reviews", unit_id)
        if store.versions(BOOK_ID):
            raise ContractError("PR12 unit already has an immutable visual review")
        record = store.put(BOOK_ID, payload)
        if payload["result"] != "PASS":
            correction = {
                "schema_version": "1.0",
                "milestone": "PR12",
                "book_id": BOOK_ID,
                "unit_id": unit_id,
                "page_id": request["page_id"],
                "failed_image_sha256": request["image_sha256"],
                "visual_review_hash": validation["review_hash"],
                "result": payload["result"],
                "localized_findings": deepcopy(payload["findings"]),
                "targeted_correction_instructions": deepcopy(payload["correction_instructions"]),
                "generation_retry_authorized": False,
                "remaining_campaign_image_operations": MAXIMUM_OPERATIONS - len(self._latest_records("autonomous-pilot-image-receipts")),
                "pr6_counter_reset": False,
                "pr11_counter_reset": False,
                "preserve_other_units": True,
                "publication_eligible": False,
            }
            self._store("autonomous-pilot-correction-requests", unit_id).put(BOOK_ID, correction)
        status = self._status(plan_record, request_record)
        _write_if_changed(self.status_path, status)
        return {"status": status["status"], "review": record, "run": status}

    def status(self):
        plan_record, request_record = self._validate_stored()
        status = self._status(plan_record, request_record)
        if self.status_path.is_file() and load_json(self.status_path) != status:
            raise ContractError("materialized PR12 status is stale")
        return {"status": status["status"], "run": status}
