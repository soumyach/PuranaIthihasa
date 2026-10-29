"""Bounded DM02 visual-proof campaign controls.

This module extends the existing immutable campaign/approval/receipt pattern to
the four proof-first units already frozen in DM02 storyboard v2.  It does not
authorize the remaining complete-book campaign, retries, publication, or a paid
provider.  The Codex host tool remains a session handoff: the repository only
prepares exact requests and validates returned pixels and receipts.
"""

from __future__ import annotations

import base64
import html
from copy import deepcopy
from pathlib import Path

from .approvals import ApprovalStore
from .errors import ContractError
from .illustration_production import inspect_png
from .util import atomic_json_write, atomic_write, content_hash, load_json, sha256_bytes, utc_now
from .versioning import ImmutableVersionStore


BOOK_ID = "DM02"
CAMPAIGN_HASH = "0465f0111d3fac1729014bb95ac5247e417aaf3429672ebc5f69e79f18fdac1e"
SUBJECT_HASH = "022e685794c7a807a2850c0522791db72944f52e785355b0f396d7ea4e49ee69"
CAMPAIGN_ID = "dm02-visual-proof-campaign-01"
MAXIMUM_OPERATIONS = 4
PANEL_IDS = ("p01-panel-01", "p11-panel-01", "p14-panel-01", "p21-panel-01")

REVIEW_DIMENSIONS = (
    "SOURCE_FIDELITY",
    "THEOLOGICAL_ACCURACY",
    "CULTURAL_AUTHENTICITY",
    "CHARACTER_IDENTITY",
    "EVENT_ACTION_DEPICTION",
    "ANATOMY",
    "NARRATIVE_CLARITY",
    "EMOTIONAL_EXPRESSIVENESS",
    "VISUAL_COMPOSITION",
    "GOLD_STANDARD_ALIGNMENT",
    "LETTERING_COMPATIBILITY",
)

REQUIRED_CONDITIONS = {
    "PRIVATE_INTERNAL_ONLY",
    "PUBLICATION_REMAINS_BLOCKED",
    "BUILT_IN_CODEX_IMAGE_TOOL_ONLY",
    "INCLUDED_ALLOWANCE_FIRST",
    "NO_SEPARATELY_BILLED_API_OR_EXTERNAL_PROVIDER",
    "NO_PURCHASED_CREDIT_CONSUMPTION_INTENDED",
    "FOUR_OPERATIONS_TOTAL_CEILING",
    "ONE_OPERATION_PER_UNIT_NO_AUTOMATIC_RETRY",
    "EXACT_REFERENCE_RECEIPTS_REQUIRED",
    "INDEPENDENT_ACTUAL_PIXEL_REVIEW_REQUIRED",
    "PRIVATE_ILLUSTRATION_CLEARANCE_EXPLICIT",
    "REMAINING_THIRTY_ONE_INITIAL_OPERATIONS_NOT_AUTHORIZED",
}

REFERENCE_SELECTION = {
    "p01-panel-01": ("kgs-satya-p01", "kgs-dm08-p09"),
    "p11-panel-01": ("kgs-satya-p01", "kgs-dm08-p12"),
    "p14-panel-01": ("kgs-satya-p01", "kgs-dm08-p21"),
    "p21-panel-01": ("kgs-satya-p01", "kgs-dm08-p28"),
}

PROMPTS = {
    "p01-panel-01": (
        "Create one clean portrait 3:4 illustration for DM02 p01-panel-01, without any page border or text. "
        "Show a wide eye-level listening triangle in a quiet forest-hermitage clearing at dusk: Sage Medhas "
        "faces Suratha and Samadhi across a low fire. Medhas is the speaking focus, an aged sage in modest "
        "bark-brown and warm-ivory clothing, seated with one measured open-hand narration gesture. Suratha has "
        "travel-worn royal bearing and a muted peacock-blue cloak but no crown, status weapon or regalia. Samadhi "
        "wears plain earth-toned clothing with no status ornament or weapon. Both listeners show neutral, attentive "
        "posture only—no invented emotion or motive. Frame the clearing with two tree trunks and warm firelight, "
        "with the complete upper 18 percent calm and uncluttered for later editable lettering. REFERENCE A supplies "
        "only premium Khatakshetra devotional painterly finish, jewel-toned Indian visual language and cinematic "
        "depth. REFERENCE B supplies only speaker-listener staging and expressive comic clarity. Do not copy any "
        "benchmark deity, lion, architecture, costume identity, plot content, text, frame or ornament. No embedded "
        "lettering, speech balloons, watermark, modern object, halo, weapon, Western fantasy armor or extra figures."
    ),
    "p11-panel-01": (
        "Create one immersive portrait 3:4 illustration for DM02 p11-panel-01, without any page border or text. "
        "On the unchanged cosmic flood, sleeping Vishnu remains supported above the waters by Shesha while Brahma "
        "remains seated on the lotus and Madhu and Kaitabha remain visibly separate and nearby. Render one exact, "
        "source-grounded withdrawal event: six distinct, modest, non-anatomical streams of radiance leave Vishnu's "
        "eyes, mouth, nose, arms, heart and breast, then gather as Yoganidra/Mahamaya, a separate dignified radiant "
        "presence appearing before Brahma. Make all six named locus groups visually readable without labels, cutaway "
        "anatomy, a seventh locus, or any suggestion of permanent bodily residence. Yoganidra has a restrained "
        "indigo-and-warm-gold presence with source-neutral anatomy, no fixed conventional arm count, no halo and no "
        "weapon array. Keep Shesha's exact hood count unspecified and unobtrusive. Reserve the complete upper 18 "
        "percent as quiet negative space for later editable lettering. REFERENCE A supplies only premium devotional "
        "painterly finish and cinematic depth. REFERENCE B supplies only the clarity and scale of a divine reveal; "
        "copy none of its Kali/Chamunda identity, skulls, tongue, weapons, army, flags, gore, text, frame or plot. No "
        "embedded lettering, balloons, watermark, modern objects, Western fantasy armor or invented divine symbols."
    ),
    "p14-panel-01": (
        "Create one clean portrait 3:4 action illustration for DM02 p14-panel-01, without any page border or text. "
        "On an unbounded midnight cosmic-water expanse, stage a readable three-figure arm-to-arm action triangle. "
        "Madhu, broad and low with an oxblood-and-charcoal silhouette, drives forward. Vishnu, in the stable "
        "midnight-blue, antique-gold and warm-ivory proposal palette, checks Madhu with one anatomically coherent "
        "grappling hold. Kaitabha, taller and angular in charcoal and deep crimson, stays a separate flank threat and "
        "does not merge with Madhu. Use humanlike combat anatomy and only scene-required arms. No one carries a "
        "weapon; show no army, chariot, injury or ordinary shoreline. Hard gold edge light and wave rings make the "
        "cause-and-effect action clear without depicting five thousand literal repetitions. Keep the complete upper "
        "18 percent uncluttered for later editable lettering. REFERENCE A supplies only premium Khatakshetra Indian "
        "devotional painterly finish and cinematic depth. REFERENCE B supplies only large-scale action clarity and "
        "foreground-to-background energy; copy none of its Raktabija identity, blood mechanism, army, elephant, "
        "weapons, flags, helmets, text, frame or theology. No embedded lettering, balloons, watermark, gore, halo, "
        "Western fantasy armor, invented emblems or extra figures."
    ),
    "p21-panel-01": (
        "Create one decisive full-page portrait 3:4 illustration for DM02 p21-panel-01, without any page border or "
        "text. The prior page has already established that the demons' condition is satisfied. Show a source-neutral "
        "unflooded-earth field that remains wholly separate from every body and visibly interrupts the surrounding "
        "cosmic flood. Its size, mechanism and cosmography remain unspecified; it is not an invented island. Vishnu "
        "raises the one source-authorized discus, and its swift luminous circle ends the threat through silhouettes "
        "and motion only. Madhu and Kaitabha remain distinct. Show no wound, anatomical impact point, thigh, lap, "
        "buttocks or other bodily platform, and no graphic gore. Vishnu uses only scene-required arms; add no other "
        "weapons or attributes. Use restrained gold edge light over midnight water and a clear before-to-consequence "
        "visual flow, while reserving the complete upper 18 percent for later editable lettering. REFERENCE A supplies "
        "only premium Khatakshetra devotional painterly finish and cinematic sacred focus. REFERENCE B supplies only "
        "climactic visual hierarchy and resolution energy; copy none of its Chandika/Chamunda/Mothers/Raktabija "
        "identities, lion, blood, weapons, flags, army, text, frame or theology. No embedded lettering, balloons, "
        "watermark, halo, Western fantasy armor, invented emblems or unrelated figures."
    ),
}


def _unsigned_hash(record, hash_field):
    return content_hash({key: value for key, value in record.items() if key != hash_field})


def _write_if_changed(path, value):
    path = Path(path)
    if path.is_file() and load_json(path) == value:
        return False
    atomic_json_write(path, value)
    return True


class DM02VisualProofCampaign:
    """Execute only the four authorized proof-first DM02 image operations."""

    def __init__(self, repository_root):
        self.root = Path(repository_root).resolve()
        self.books_root = self.root / "books"
        self.book_root = self.books_root / BOOK_ID
        self.campaign_path = self.book_root / "image-campaigns" / (CAMPAIGN_HASH + ".request.json")
        self.approvals = ApprovalStore(self.book_root / "approvals")
        self.clearance_store = ImmutableVersionStore(self.books_root, "private-illustration-clearances")
        self.usage_store = ImmutableVersionStore(self.books_root, "visual-proof-usage-observations")
        self.status_path = self.book_root / "visual-proof-campaign-status.json"

    def _store(self, kind, panel_id):
        if panel_id not in PANEL_IDS:
            raise ContractError("panel is outside the bounded DM02 visual-proof campaign", {"panel_id": panel_id})
        return ImmutableVersionStore(self.books_root, "%s/%s" % (kind, panel_id))

    def _campaign(self):
        if not self.campaign_path.is_file():
            raise ContractError("the exact optimized DM02 image campaign is missing")
        campaign = load_json(self.campaign_path)
        if campaign.get("campaign_hash") != CAMPAIGN_HASH:
            raise ContractError("DM02 campaign identity is stale")
        if _unsigned_hash(campaign, "campaign_hash") != CAMPAIGN_HASH:
            raise ContractError("DM02 campaign content hash is invalid")
        if campaign.get("authorization_subject_hash") != SUBJECT_HASH:
            raise ContractError("DM02 campaign authorization subject is stale")
        if campaign.get("status") != "AWAITING_CAMPAIGN_AUTHORIZATION":
            raise ContractError("the preserved complete-book campaign status changed unexpectedly")
        proof_first = campaign.get("generation_plan", {}).get("proof_first_panel_ids")
        if proof_first != list(PANEL_IDS):
            raise ContractError("DM02 proof-first panel order changed")
        units = {unit["panel_id"]: unit for unit in campaign.get("units", []) if unit.get("panel_id") in PANEL_IDS}
        if list(units) != list(PANEL_IDS):
            raise ContractError("DM02 campaign does not contain the exact four proof-first units")
        return campaign, units

    def _approval(self):
        return self.approvals.find_valid(
            "PRODUCTION_CAMPAIGN", SUBJECT_HASH, {"type": "book", "id": BOOK_ID},
            target_context={"source_scope": "dm-source", "tradition_id": "devi-mahatmyam", "edition_id": "pargiter-1904"},
            current_evidence_hash=SUBJECT_HASH,
        )

    def _clearance(self):
        records = self.clearance_store.versions(BOOK_ID)
        if not records:
            return None
        payload = records[-1]["payload"]
        if (
            payload.get("decision") != "PASS"
            or payload.get("campaign_hash") != CAMPAIGN_HASH
            or payload.get("authorization_subject_hash") != SUBJECT_HASH
            or payload.get("authorized_panel_ids") != list(PANEL_IDS)
            or payload.get("maximum_image_operations") != MAXIMUM_OPERATIONS
            or payload.get("retries_authorized") is not False
        ):
            raise ContractError("stored DM02 private-illustration clearance is stale or overbroad")
        return records[-1]

    def _latest_records(self, kind):
        result = {}
        for panel_id in PANEL_IDS:
            versions = self._store(kind, panel_id).versions(BOOK_ID)
            if len(versions) > 1:
                raise ContractError("DM02 one-operation/review ceiling was exceeded", {"kind": kind, "panel_id": panel_id})
            if versions:
                result[panel_id] = versions[-1]
        return result

    def _usage_by_phase(self):
        result = {}
        for record in self.usage_store.versions(BOOK_ID):
            phase = record["payload"].get("phase")
            if phase in result:
                raise ContractError("DM02 usage phase was recorded more than once", {"phase": phase})
            result[phase] = record
        return result

    def _reference_manifest(self):
        path = self.root / "book-factory" / "references" / "visual-gold-standard" / "manifest.json"
        manifest = load_json(path)
        references = {item["reference_id"]: item for item in manifest.get("pages", [])}
        return path, references

    def _references(self, panel_id):
        _manifest_path, references = self._reference_manifest()
        selected = REFERENCE_SELECTION[panel_id]
        roles = ("A_SERIES_VISUAL_IDENTITY", "B_PAGE_PANEL_COMPOSITION")
        result = []
        for reference_id, role in zip(selected, roles):
            item = references.get(reference_id)
            if not item:
                raise ContractError("selected PR7 reference is absent", {"reference_id": reference_id})
            relative = item["extracted_path"]
            path = self.root / relative
            if not path.is_file() or sha256_bytes(path.read_bytes()) != item["extracted_sha256"]:
                raise ContractError("selected PR7 reference pixels are missing or changed", {"reference_id": reference_id})
            result.append({
                "role": role,
                "reference_id": reference_id,
                "path": relative,
                "sha256": item["extracted_sha256"],
                "approval_status": "CURATED_PRESENTATION_REFERENCE_NOT_SOURCE_AUTHORITY",
                "content_transfer": "FORBIDDEN",
                "available": True,
            })
        result.extend([
            {
                "role": "C_APPROVED_CHARACTER_REFERENCE",
                "available": False,
                "approval_status": "UNAVAILABLE_NO_INDEPENDENTLY_APPROVED_DM02_CHARACTER_PIXELS",
                "content_transfer": "NOT_APPLICABLE",
            },
            {
                "role": "D_APPROVED_SETTING_REFERENCE",
                "available": False,
                "approval_status": "UNAVAILABLE_NO_INDEPENDENTLY_APPROVED_DM02_SETTING_PIXELS",
                "content_transfer": "NOT_APPLICABLE",
            },
        ])
        return result

    def _status(self):
        _campaign, _units = self._campaign()
        approval = self._approval()
        clearance = self._clearance()
        images = self._latest_records("visual-proof-image-receipts")
        reviews = self._latest_records("visual-proof-reviews")
        usage = self._usage_by_phase()
        if not approval or not clearance:
            lifecycle = "AWAITING_CAMPAIGN_AUTHORIZATION"
        elif "BEFORE" not in usage:
            lifecycle = "AUTHORIZED_AWAITING_USAGE_PREFLIGHT"
        elif len(images) < MAXIMUM_OPERATIONS:
            lifecycle = "AUTHORIZED_AWAITING_IMAGE_OPERATIONS"
        elif len(reviews) < MAXIMUM_OPERATIONS:
            lifecycle = "GENERATED_AWAITING_INDEPENDENT_VISUAL_REVIEW"
        elif "AFTER" not in usage:
            lifecycle = "REVIEWED_AWAITING_POST_USAGE_OBSERVATION"
        elif all(record["payload"]["result"] == "PASS" for record in reviews.values()):
            lifecycle = "FOUR_PROOFS_REVIEWED_PASS_CAMPAIGN_COMPLETE"
        else:
            lifecycle = "FOUR_PROOFS_REVIEWED_WITH_BLOCKERS_CAMPAIGN_COMPLETE_NO_RETRY"
        status = {
            "schema_version": "1.0",
            "book_id": BOOK_ID,
            "campaign_id": CAMPAIGN_ID,
            "preserved_complete_book_campaign_hash": CAMPAIGN_HASH,
            "campaign_subject_hash": SUBJECT_HASH,
            "status": lifecycle,
            "approval_id": approval.get("id") if approval else None,
            "private_illustration_clearance_record_hash": clearance.get("content_hash") if clearance else None,
            "generation_authorized": bool(approval and clearance),
            "authorized_panel_ids": list(PANEL_IDS),
            "operation_ceiling": MAXIMUM_OPERATIONS,
            "image_operations_executed": len(images),
            "remaining_authorized_operations": MAXIMUM_OPERATIONS - len(images),
            "automatic_retries_authorized": False,
            "remaining_complete_book_initial_operations_authorized": 0,
            "independent_reviews_completed": len(reviews),
            "review_results": {panel_id: record["payload"]["result"] for panel_id, record in reviews.items()},
            "usage_before_record_hash": usage.get("BEFORE", {}).get("content_hash"),
            "usage_after_record_hash": usage.get("AFTER", {}).get("content_hash"),
            "actual_incremental_usd": "UNKNOWN_NOT_EXPOSED" if images else "NOT_APPLICABLE_NO_OPERATION",
            "separately_billed_provider_calls": 0,
            "purchased_credit_consumption": "NOT_REQUESTED_OR_REPORTED",
            "publication_eligible": False,
            "pdf_authorized": False,
            "full_book_generation_authorized": False,
        }
        status["status_hash"] = _unsigned_hash(status, "status_hash")
        return status

    def import_authorization(self, authorization_path):
        self._campaign()
        proposed = load_json(Path(authorization_path))
        exact = {
            "approval_type": "PRODUCTION_CAMPAIGN",
            "subject_type": "PRODUCTION_CAMPAIGN",
            "subject_hash": SUBJECT_HASH,
            "scope": {"type": "book", "id": BOOK_ID},
            "decision": "PASS",
        }
        for key, expected in exact.items():
            if proposed.get(key) != expected:
                raise ContractError("DM02 authorization does not match the exact campaign", {"field": key})
        approver = proposed.get("approver", {})
        if "PRIVATE_INTERNAL_VISUAL_TESTING" not in approver.get("authority", []):
            raise ContractError("DM02 approver lacks private visual-testing authority")
        conditions = set(proposed.get("conditions", []))
        if not REQUIRED_CONDITIONS.issubset(conditions):
            raise ContractError("DM02 authorization omits required fail-closed conditions")
        if proposed.get("maximum_paid_spend_minor_units") != 0:
            raise ContractError("DM02 authorization must retain the zero-spend cap")
        clearance = proposed.get("private_illustration_clearance", {})
        if (
            clearance.get("decision") != "PASS"
            or clearance.get("authorized_panel_ids") != list(PANEL_IDS)
            or clearance.get("maximum_image_operations") != MAXIMUM_OPERATIONS
            or clearance.get("retries_authorized") is not False
            or clearance.get("publication_authorized") is not False
        ):
            raise ContractError("DM02 private-illustration clearance is absent or overbroad")
        evidence_path = Path(clearance.get("user_authorization_evidence_path", ""))
        if not evidence_path.is_absolute():
            evidence_path = self.root / evidence_path
        if not evidence_path.is_file():
            raise ContractError("DM02 user-authorization evidence is missing")
        evidence_sha = sha256_bytes(evidence_path.read_bytes())
        if evidence_sha != clearance.get("user_authorization_evidence_sha256"):
            raise ContractError("DM02 user-authorization evidence hash is stale")
        clearance_payload = {
            "schema_version": "1.0",
            "book_id": BOOK_ID,
            "decision": "PASS",
            "purpose": "BOUNDED_PRIVATE_INTERNAL_ILLUSTRATION_TEST",
            "campaign_hash": CAMPAIGN_HASH,
            "authorization_subject_hash": SUBJECT_HASH,
            "authorized_panel_ids": list(PANEL_IDS),
            "maximum_image_operations": MAXIMUM_OPERATIONS,
            "retries_authorized": False,
            "publication_authorized": False,
            "pdf_authorized": False,
            "full_book_generation_authorized": False,
            "provider_id": "codex-built-in-image-gen",
            "conditions": sorted(conditions),
            "approver": deepcopy(approver),
            "user_authorization_evidence_path": str(evidence_path),
            "user_authorization_evidence_sha256": evidence_sha,
            "recorded_at": utc_now(),
        }
        existing_clearances = self.clearance_store.versions(BOOK_ID)
        if existing_clearances:
            comparable = dict(clearance_payload)
            comparable.pop("recorded_at", None)
            stored = dict(existing_clearances[-1]["payload"])
            stored.pop("recorded_at", None)
            if stored != comparable:
                raise ContractError("DM02 private-illustration clearance already exists with different scope")
            clearance_record = existing_clearances[-1]
        else:
            clearance_record = self.clearance_store.put(BOOK_ID, clearance_payload)
        approval = self.approvals.create(
            proposed["approval_type"], proposed["subject_type"], proposed["subject_hash"], proposed["scope"],
            approver, proposed.get("creator", {"id": "dm02-visual-proof-director"}), proposed["decision"],
            inheritance_allowed=False, conditions=sorted(conditions),
            invalidators=["campaign_hash", "cost_policy", "provider", "reference_hash", "unit_prompt_hash"],
            evidence_refs=[CAMPAIGN_HASH, clearance_record["content_hash"], evidence_sha],
            source_scope="dm-source", tradition_id="devi-mahatmyam", edition_id="pargiter-1904",
            evidence_hash=SUBJECT_HASH, expires_at=proposed.get("expires_at"),
        )
        status = self._status()
        _write_if_changed(self.status_path, status)
        return {"status": status["status"], "approval": approval, "clearance": clearance_record, "run": status}

    def record_usage_observation(self, phase, observation_path):
        phase = phase.upper()
        if phase not in {"BEFORE", "AFTER"}:
            raise ContractError("DM02 usage phase must be BEFORE or AFTER")
        current = self._usage_by_phase()
        if phase in current:
            return {"status": "IDEMPOTENT_REPLAY", "record": current[phase], "run": self._status()}
        if phase == "AFTER" and len(self._latest_records("visual-proof-image-receipts")) != MAXIMUM_OPERATIONS:
            raise ContractError("post-campaign usage observation requires all four one-shot operations")
        path = Path(observation_path)
        observation = load_json(path)
        if observation.get("ordinaryUsageAllowed") is not True:
            raise ContractError("Codex ordinary usage is not currently allowed")
        codex = observation.get("rateLimitsByLimitId", {}).get("codex") or observation.get("rateLimits")
        if not isinstance(codex, dict):
            raise ContractError("Codex usage observation lacks the active allowance bucket")
        credits = codex.get("credits", {})
        if credits.get("hasCredits") is True or str(credits.get("balance", "0")) not in {"0", "0.0", "0.00"}:
            raise ContractError("DM02 included-allowance-first policy cannot use a purchased-credit balance")
        payload = {
            "schema_version": "1.0",
            "book_id": BOOK_ID,
            "campaign_id": CAMPAIGN_ID,
            "phase": phase,
            "observation": observation,
            "source_path": str(path.resolve()),
            "source_sha256": sha256_bytes(path.read_bytes()),
            "recorded_at": utc_now(),
        }
        records = self.usage_store.versions(BOOK_ID)
        record = self.usage_store.put(BOOK_ID, payload, records[-1]["content_hash"] if records else None)
        status = self._status()
        _write_if_changed(self.status_path, status)
        return {"status": status["status"], "record": record, "run": status}

    def prepare_generation(self, panel_id):
        campaign, units = self._campaign()
        approval = self._approval()
        clearance = self._clearance()
        if not approval or not clearance:
            raise ContractError("DM02 generation requires exact approval and private-illustration clearance")
        if "BEFORE" not in self._usage_by_phase():
            raise ContractError("DM02 generation requires a fresh before-campaign allowance observation")
        if panel_id not in PANEL_IDS:
            raise ContractError("panel is outside the authorized DM02 proof set", {"panel_id": panel_id})
        images = self._latest_records("visual-proof-image-receipts")
        if len(images) >= MAXIMUM_OPERATIONS:
            raise ContractError("DM02 four-operation ceiling is exhausted")
        store = self._store("visual-proof-generation-requests", panel_id)
        if store.versions(BOOK_ID):
            raise ContractError("DM02 proof unit already has a prepared one-shot operation", {"panel_id": panel_id})
        unit = units[panel_id]
        request = {
            "schema_version": "1.0",
            "book_id": BOOK_ID,
            "campaign_id": CAMPAIGN_ID,
            "preserved_complete_book_campaign_hash": campaign["campaign_hash"],
            "campaign_subject_hash": SUBJECT_HASH,
            "campaign_approval_id": approval["id"],
            "private_illustration_clearance_record_hash": clearance["content_hash"],
            "unit_id": unit["unit_id"],
            "page_id": unit["page_id"],
            "page_number": unit["page_number"],
            "panel_id": panel_id,
            "operation": "generate",
            "required_action": unit["required_action"],
            "character_ids": deepcopy(unit["character_ids"]),
            "location_id": unit["location_id"],
            "safe_regions": deepcopy(unit["safe_regions"]),
            "prompt": PROMPTS[panel_id],
            "prompt_sha256": content_hash(PROMPTS[panel_id]),
            "references": self._references(panel_id),
            "provider_id": "codex-built-in-image-gen",
            "provider_interface": "referenced_image_paths",
            "text_in_image": False,
            "maximum_operations_for_unit": 1,
            "maximum_paid_spend_minor_units": 0,
            "automatic_retry_authorized": False,
            "character_consistency_certified": False,
        }
        request["request_hash"] = _unsigned_hash(request, "request_hash")
        record = store.put(BOOK_ID, request)
        return {"status": "READY_FOR_ONE_HOST_IMAGE_OPERATION", "record": record, "request": request}

    def import_image(self, panel_id, request_path, image_path, provider_receipt_path):
        if not self._approval() or not self._clearance():
            raise ContractError("DM02 image import requires exact approval and private-illustration clearance")
        requests = self._store("visual-proof-generation-requests", panel_id).versions(BOOK_ID)
        if len(requests) != 1 or load_json(Path(request_path)) != requests[0]:
            raise ContractError("DM02 image import does not bind its immutable prepared request")
        store = self._store("visual-proof-image-receipts", panel_id)
        if store.versions(BOOK_ID):
            return {"status": "IDEMPOTENT_REPLAY", "record": store.versions(BOOK_ID)[0], "run": self._status()}
        existing = self._latest_records("visual-proof-image-receipts")
        if len(existing) >= MAXIMUM_OPERATIONS:
            raise ContractError("DM02 four-operation ceiling is exhausted")
        request = requests[0]["payload"]
        provider = load_json(Path(provider_receipt_path))
        for key, expected in {
            "provider_id": request["provider_id"],
            "panel_id": panel_id,
            "unit_id": request["unit_id"],
            "operation": "generate",
            "request_hash": request["request_hash"],
            "campaign_subject_hash": SUBJECT_HASH,
        }.items():
            if provider.get(key) != expected:
                raise ContractError("DM02 provider receipt does not bind the authorized operation", {"field": key})
        if any(provider.get(field) for field in (
            "api_key_supplied", "external_provider_authorization_requested", "paid_billing_requested",
            "automatic_credit_purchase_requested",
        )):
            raise ContractError("DM02 receipt reports a forbidden billing or provider path")
        if provider.get("purchased_credit_consumption") not in {"NOT_REQUESTED", "NOT_REPORTED_NO_BALANCE", "NOT_REQUESTED_OR_REPORTED"}:
            raise ContractError("DM02 receipt violates purchased-credit policy")
        if provider.get("actual_incremental_usd") != "UNKNOWN_NOT_EXPOSED":
            raise ContractError("DM02 must not invent a zero-dollar result")
        if provider.get("included_allowance_policy") != "CURRENT_INCLUDED_ALLOWANCE_FIRST":
            raise ContractError("DM02 receipt omits included-allowance-first policy")
        if provider.get("retry") is not False:
            raise ContractError("DM02 provider receipt attempts an unauthorized retry")
        if provider.get("submitted_prompt") != request["prompt"] or provider.get("submitted_prompt_sha256") != request["prompt_sha256"]:
            raise ContractError("DM02 receipt does not preserve the exact submitted prompt")
        expected_refs = [item for item in request["references"] if item.get("available")]
        submitted_refs = provider.get("submitted_references", [])
        keys = ("role", "reference_id", "path", "sha256")
        if [{key: item.get(key) for key in keys} for item in submitted_refs] != [
            {key: item.get(key) for key in keys} for item in expected_refs
        ]:
            raise ContractError("DM02 reference receipt differs from the authorized A/B inputs")
        image_path = Path(image_path).resolve()
        try:
            relative = image_path.relative_to(self.root).as_posix()
        except ValueError as exc:
            raise ContractError("DM02 image must be preserved inside the repository") from exc
        expected_prefix = "books/DM02/visual-proof-campaign/images/%s/" % panel_id
        if not relative.startswith(expected_prefix):
            raise ContractError("DM02 image is outside its panel-specific directory")
        image = inspect_png(image_path)
        if image["sha256"] != provider.get("output_sha256"):
            raise ContractError("DM02 receipt output hash does not match actual pixels")
        if image["sha256"] in {record["payload"]["image"]["sha256"] for record in existing.values()}:
            raise ContractError("DM02 proof image duplicates a prior campaign output")
        payload = {
            "schema_version": "1.0",
            "book_id": BOOK_ID,
            "campaign_id": CAMPAIGN_ID,
            "campaign_subject_hash": SUBJECT_HASH,
            "unit_id": request["unit_id"],
            "page_id": request["page_id"],
            "page_number": request["page_number"],
            "panel_id": panel_id,
            "operation": "generate",
            "generation_request_record_hash": requests[0]["content_hash"],
            "request_hash": request["request_hash"],
            "provider": deepcopy(provider),
            "image": dict(image, path=relative),
            "producer_ids": [provider["producer"]["id"]],
            "status": "GENERATED_AWAITING_INDEPENDENT_VISUAL_REVIEW",
            "publication_eligible": False,
            "character_consistency_certified": False,
            "imported_at": utc_now(),
        }
        record = store.put(BOOK_ID, payload)
        status = self._status()
        _write_if_changed(self.status_path, status)
        return {"status": payload["status"], "record": record, "image": payload["image"], "run": status}

    def prepare_visual_review(self, panel_id):
        images = self._latest_records("visual-proof-image-receipts")
        if panel_id not in images:
            raise ContractError("DM02 review requires imported real pixels", {"panel_id": panel_id})
        receipt = images[panel_id]["payload"]
        store = self._store("visual-proof-review-requests", panel_id)
        if store.versions(BOOK_ID):
            record = store.versions(BOOK_ID)[0]
        else:
            request = {
                "schema_version": "1.0",
                "book_id": BOOK_ID,
                "campaign_id": CAMPAIGN_ID,
                "campaign_subject_hash": SUBJECT_HASH,
                "unit_id": receipt["unit_id"],
                "page_id": receipt["page_id"],
                "panel_id": panel_id,
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
        return {"status": "AWAITING_INDEPENDENT_ACTUAL_PIXEL_REVIEW", "record": record, "run": self._status()}

    def import_visual_review(self, panel_id, request_path, response_path):
        requests = self._store("visual-proof-review-requests", panel_id).versions(BOOK_ID)
        if len(requests) != 1 or load_json(Path(request_path)) != requests[0]:
            raise ContractError("DM02 review response does not bind its immutable request")
        request = requests[0]["payload"]
        response = load_json(Path(response_path))
        if response.get("request_hash") != request["request_hash"] or response.get("panel_id") != panel_id:
            raise ContractError("DM02 visual review response is stale or targets another panel")
        if response.get("image_sha256") != request["image_sha256"]:
            raise ContractError("DM02 visual review does not bind the exact image")
        reviewer = response.get("reviewer", {})
        if not reviewer.get("image_capable") or not reviewer.get("inspected_actual_pixels"):
            raise ContractError("DM02 visual review did not inspect actual pixels")
        if reviewer.get("reading_size") != "ACTUAL_READING_SIZE":
            raise ContractError("DM02 visual review omitted actual reading-size inspection")
        if reviewer.get("id") in set(request["producer_ids"]):
            raise ContractError("DM02 reviewer is not independent from the producer")
        assessments = response.get("assessments", [])
        if [item.get("dimension") for item in assessments] != list(REVIEW_DIMENSIONS):
            raise ContractError("DM02 review dimensions are incomplete or out of order")
        results = [item.get("result") for item in assessments]
        if any(value not in {"PASS", "FIX", "ESCALATE"} for value in results):
            raise ContractError("DM02 review contains an invalid dimension result")
        result = "ESCALATE" if "ESCALATE" in results else "FIX" if "FIX" in results else "PASS"
        if response.get("overall_verdict") != result:
            raise ContractError("DM02 review verdict conflicts with dimension results")
        findings = response.get("findings", [])
        if result != "PASS" and not findings:
            raise ContractError("non-PASS DM02 review requires specific findings")
        payload = {
            "schema_version": "1.0",
            "book_id": BOOK_ID,
            "campaign_id": CAMPAIGN_ID,
            "campaign_subject_hash": SUBJECT_HASH,
            "unit_id": request["unit_id"],
            "page_id": request["page_id"],
            "panel_id": panel_id,
            "request_record_hash": requests[0]["content_hash"],
            "request_hash": request["request_hash"],
            "image_path": request["image_path"],
            "image_sha256": request["image_sha256"],
            "comparison_references": deepcopy(request["comparison_references"]),
            "reviewer": deepcopy(reviewer),
            "assessments": deepcopy(assessments),
            "findings": deepcopy(findings),
            "correction_instructions": deepcopy(response.get("correction_instructions", [])),
            "result": result,
            "review_hash": content_hash(response),
            "independent_actual_pixel_review": True,
            "character_reference_promoted": False,
            "setting_reference_promoted": False,
            "publication_eligible": False,
            "generation_retry_authorized": False,
            "reviewed_at": utc_now(),
        }
        store = self._store("visual-proof-reviews", panel_id)
        if store.versions(BOOK_ID):
            raise ContractError("DM02 panel already has an immutable visual review")
        record = store.put(BOOK_ID, payload)
        status = self._status()
        _write_if_changed(self.status_path, status)
        return {"status": status["status"], "review": record, "run": status}

    def build_contact_sheet(self):
        images = self._latest_records("visual-proof-image-receipts")
        if list(images) != list(PANEL_IDS):
            raise ContractError("DM02 contact sheet requires all four exact proof images")
        reviews = self._latest_records("visual-proof-reviews")
        cards = []
        for panel_id in PANEL_IDS:
            receipt = images[panel_id]["payload"]
            path = self.root / receipt["image"]["path"]
            actual = inspect_png(path)
            if actual["sha256"] != receipt["image"]["sha256"]:
                raise ContractError("DM02 contact-sheet image hash is stale", {"panel_id": panel_id})
            encoded = base64.b64encode(path.read_bytes()).decode("ascii")
            cards.append((panel_id, receipt, reviews.get(panel_id), encoded))
        width, card_width, card_height = 2320, 1086, 1700
        height = 120 + 2 * card_height + 80
        fragments = [
            '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">' % (width, height, width, height),
            '<rect width="100%" height="100%" fill="#071F35"/>',
            '<text x="80" y="70" fill="#F0CF76" font-family="Georgia,serif" font-size="38">DM02 — Four Visual Proofs</text>',
        ]
        for index, (panel_id, receipt, review, encoded) in enumerate(cards):
            column, row = index % 2, index // 2
            x, y = 60 + column * 1140, 110 + row * card_height
            fragments.extend([
                '<rect x="%d" y="%d" width="%d" height="1645" rx="10" fill="#FFF9EF" stroke="#D8AC4E" stroke-width="8"/>' % (x, y, card_width),
                '<image x="%d" y="%d" width="966" height="1288" preserveAspectRatio="xMidYMid meet" href="data:image/png;base64,%s"/>' % (x + 60, y + 50, encoded),
            ])
            metadata = [
                "Panel: %s" % panel_id,
                "Page: %s" % receipt["page_id"],
                "Image: %s" % receipt["image"]["sha256"][:24],
                "Dimensions: %dx%d" % (receipt["image"]["width"], receipt["image"]["height"]),
                "Visual QA: %s" % (review["payload"]["result"] if review else "PENDING"),
                "Character reference approval: NOT PROMOTED",
            ]
            for line_number, line in enumerate(metadata):
                fragments.append(
                    '<text x="%d" y="%d" fill="#251C18" font-family="Georgia,serif" font-size="24">%s</text>'
                    % (x + 60, y + 1380 + line_number * 40, html.escape(line))
                )
        fragments.append("</svg>")
        destination = self.book_root / "visual-proof-campaign" / "contact-sheet.svg"
        atomic_write(destination, ("\n".join(fragments) + "\n").encode("utf-8"))
        payload = {
            "schema_version": "1.0",
            "book_id": BOOK_ID,
            "campaign_id": CAMPAIGN_ID,
            "path": destination.relative_to(self.root).as_posix(),
            "sha256": sha256_bytes(destination.read_bytes()),
            "format": "SVG_WITH_EMBEDDED_UNMODIFIED_PNG_PIXELS",
            "panels": [
                {
                    "panel_id": panel_id,
                    "image_path": images[panel_id]["payload"]["image"]["path"],
                    "image_sha256": images[panel_id]["payload"]["image"]["sha256"],
                    "visual_review": reviews.get(panel_id, {}).get("payload", {}).get("result", "PENDING"),
                }
                for panel_id in PANEL_IDS
            ],
            "publication_eligible": False,
        }
        store = ImmutableVersionStore(self.books_root, "visual-proof-contact-sheets")
        records = store.versions(BOOK_ID)
        record = store.put(BOOK_ID, payload, records[-1]["content_hash"] if records else None)
        return {"status": "CONTACT_SHEET_READY_PRIVATE_INTERNAL_ONLY", "record": record, "contact_sheet": payload}

    def status(self):
        status = self._status()
        if self.status_path.is_file() and load_json(self.status_path) != status:
            raise ContractError("materialized DM02 visual-proof status is stale")
        return {"status": status["status"], "run": status}
