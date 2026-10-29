"""Deterministic PR5 visual-preproduction contracts; no image generation lives here."""

import re
from pathlib import Path

from .bibles import validate_character_bible, validate_location_bible
from .errors import ContractError
from .quality import report
from .state import page_id
from .util import content_hash, sha256_bytes
from .versioning import ProofSpecVersionStore


CANVAS = {"aspect_ratio": "3:4", "pixel_width": 1086, "pixel_height": 1448}
PALETTE = {"#071F35", "#D8AC4E", "#F0CF76", "#F6E8C6", "#FFF9EF", "#251C18", "#692019"}
TEXT_CHANNELS = {"NARRATION", "DIALOGUE", "THOUGHT", "INSET_EXPLANATION"}
PROOF_KINDS = {
    "QUIET_CONVERSATION",
    "DIVINE_REVEAL",
    "BATTLE",
    "FULL_PAGE_IMMERSION",
}
REQUIRED_MOMENTS = {
    "empty_thrones_and_defeated_gods",
    "gathered_divine_radiance",
    "devi_manifestation",
    "divine_gifts_and_weapons",
    "devi_roar_and_gathering_asura_army",
    "army_from_devi_breath",
    "commander_battles",
    "mahishasura_buffalo_entrance",
    "mahishasura_changing_forms",
    "devi_decisive_victory",
    "gods_hymn_and_boon",
    "return_to_hermitage",
}


def _missing(entry, fields, code, entry_id=None):
    return [
        {"code": code, "entry_id": entry_id or entry.get("id"), "field": field}
        for field in fields if field not in entry
    ]


def _safe_region_findings(regions, owner):
    findings = []
    if not regions:
        return [{"code": "SAFE_REGION_REQUIRED", "owner": owner}]
    for region in regions:
        for field in ("id", "purpose", "x", "y", "width", "height"):
            if field not in region:
                findings.append({"code": "SAFE_REGION_FIELD_MISSING", "owner": owner, "field": field})
        for field in ("x", "y", "width", "height"):
            value = region.get(field)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0 or value > 1:
                findings.append({"code": "SAFE_REGION_OUT_OF_BOUNDS", "owner": owner, "field": field})
        if isinstance(region.get("x"), (int, float)) and isinstance(region.get("width"), (int, float)):
            if region["x"] + region["width"] > 1:
                findings.append({"code": "SAFE_REGION_OUT_OF_BOUNDS", "owner": owner, "field": "x+width"})
        if isinstance(region.get("y"), (int, float)) and isinstance(region.get("height"), (int, float)):
            if region["y"] + region["height"] > 1:
                findings.append({"code": "SAFE_REGION_OUT_OF_BOUNDS", "owner": owner, "field": "y+height"})
    return findings


def validate_storyboard(storyboard, required_event_ids, manuscript, character_bible, location_bible,
                        expected_manuscript_hash=None, required_moment_ids=None):
    findings = []
    findings.extend(_missing(storyboard, (
        "schema_version", "book_id", "version", "manuscript_hash", "canvas", "pages",
        "required_moments", "text_channels", "reading_order_policy",
    ), "STORYBOARD_FIELD_MISSING", storyboard.get("book_id")))
    if storyboard.get("canvas") != CANVAS:
        findings.append({"code": "STORYBOARD_CANVAS_MISMATCH", "expected": CANVAS})
    if expected_manuscript_hash and storyboard.get("manuscript_hash") != expected_manuscript_hash:
        findings.append({"code": "STORYBOARD_MANUSCRIPT_HASH_MISMATCH"})
    if set(storyboard.get("text_channels", [])) != TEXT_CHANNELS:
        findings.append({"code": "TEXT_CHANNEL_CONTRACT_INCOMPLETE", "required": sorted(TEXT_CHANNELS)})
    required_moments = set(REQUIRED_MOMENTS if required_moment_ids is None else required_moment_ids)
    moment_ids = [item.get("id") for item in storyboard.get("required_moments", [])]
    missing_moments = sorted(required_moments - set(moment_ids))
    if missing_moments:
        findings.append({"code": "REQUIRED_MOMENTS_MISSING", "moment_ids": missing_moments})

    character_entries = {item.get("id"): item for item in character_bible.get("entries", [])}
    location_ids = {item.get("id") for item in location_bible.get("entries", [])}
    claim_ids = {item.get("id") for item in manuscript.get("claim_map", [])}
    page_numbers = []
    page_ids = set()
    covered_events = set()
    covered_moments = set()
    full_page_count = 0
    for page in storyboard.get("pages", []):
        number = page.get("page_number")
        owner = page.get("page_id") or number
        findings.extend(_missing(page, (
            "page_id", "page_number", "title", "event_ids", "narrative_beats", "source_claim_ids",
            "character_ids", "location_id", "visual_intent", "layout", "panels", "reading_order",
            "lettering", "continuity_requirements", "image_instructions", "safe_regions",
            "validation_requirements", "moment_ids", "panel_count", "continuity_in", "continuity_out",
        ), "PAGE_FIELD_MISSING", owner))
        if isinstance(number, int):
            page_numbers.append(number)
            expected_page_id = page_id(storyboard.get("book_id"), number)
            if page.get("page_id") != expected_page_id:
                findings.append({"code": "PAGE_ID_NOT_DETERMINISTIC", "page_number": number, "expected": expected_page_id})
        if page.get("page_id") in page_ids:
            findings.append({"code": "DUPLICATE_PAGE_ID", "page_id": page.get("page_id")})
        page_ids.add(page.get("page_id"))
        covered_events.update(page.get("event_ids", []))
        covered_moments.update(page.get("moment_ids", []))
        if page.get("layout", {}).get("type") == "FULL_PAGE":
            full_page_count += 1
        if page.get("panel_count") != len(page.get("panels", [])):
            findings.append({"code": "PANEL_COUNT_MISMATCH", "page_id": owner})
        if not page.get("panels"):
            findings.append({"code": "PAGE_REQUIRES_AT_LEAST_ONE_PANEL", "page_id": owner})
        unknown_chars = sorted(set(page.get("character_ids", [])) - set(character_entries))
        if unknown_chars:
            findings.append({"code": "UNKNOWN_PAGE_CHARACTER", "page_id": owner, "character_ids": unknown_chars})
        if page.get("location_id") not in location_ids:
            findings.append({"code": "UNKNOWN_PAGE_LOCATION", "page_id": owner, "location_id": page.get("location_id")})
        unknown_claims = sorted(set(page.get("source_claim_ids", [])) - claim_ids)
        if unknown_claims:
            findings.append({"code": "UNKNOWN_PAGE_CLAIM", "page_id": owner, "claim_ids": unknown_claims})
        findings.extend(_safe_region_findings(page.get("safe_regions", []), owner))

        panel_orders = []
        for panel in page.get("panels", []):
            panel_owner = panel.get("id") or owner
            findings.extend(_missing(panel, (
                "id", "reading_order", "composition", "character_ids", "location_id",
                "visual_description", "continuity_requirements", "image_instructions", "safe_regions",
            ), "PANEL_FIELD_MISSING", panel_owner))
            panel_orders.append(panel.get("reading_order"))
            if panel.get("location_id") not in location_ids:
                findings.append({"code": "UNKNOWN_PANEL_LOCATION", "panel_id": panel_owner})
            if set(panel.get("character_ids", [])) - set(character_entries):
                findings.append({"code": "UNKNOWN_PANEL_CHARACTER", "panel_id": panel_owner})
            if panel.get("visual_description") == "Advance the same sourced action without repeating the lettering.":
                findings.append({"code": "PLACEHOLDER_PANEL_SPECIFICATION", "panel_id": panel_owner})
            instructions = panel.get("image_instructions", {})
            if not isinstance(instructions, dict) or not instructions.get("required_action"):
                findings.append({"code": "PANEL_REQUIRED_ACTION_MISSING", "panel_id": panel_owner})
            findings.extend(_safe_region_findings(panel.get("safe_regions", []), panel_owner))
        if panel_orders != list(range(1, len(panel_orders) + 1)):
            findings.append({"code": "PANEL_READING_ORDER_INVALID", "page_id": owner})

        normalized_by_channel = {}
        lettering_ids = set()
        for item in page.get("lettering", []):
            findings.extend(_missing(item, ("id", "channel", "text", "placement"), "LETTERING_FIELD_MISSING", owner))
            if item.get("id") in lettering_ids:
                findings.append({"code": "DUPLICATE_LETTERING_ID", "page_id": owner, "lettering_id": item.get("id")})
            lettering_ids.add(item.get("id"))
            channel = item.get("channel")
            if channel not in TEXT_CHANNELS:
                findings.append({"code": "UNKNOWN_TEXT_CHANNEL", "page_id": owner, "channel": channel})
            if channel in {"DIALOGUE", "THOUGHT"} and not item.get("speaker_id"):
                findings.append({
                    "code": "DIALOGUE_SPEAKER_MISSING" if channel == "DIALOGUE" else "THOUGHT_ATTRIBUTION_MISSING",
                    "page_id": owner,
                    "lettering_id": item.get("id"),
                })
            if item.get("speaker_id") and item["speaker_id"] not in character_entries:
                findings.append({"code": "UNKNOWN_DIALOGUE_SPEAKER", "page_id": owner, "speaker_id": item["speaker_id"]})
            elif item.get("speaker_id") and item["speaker_id"] not in set(page.get("character_ids", [])):
                findings.append({"code": "SPEAKER_NOT_PRESENT_ON_PAGE", "page_id": owner, "speaker_id": item["speaker_id"]})
            normalized = re.sub(r"[^a-z0-9]+", " ", item.get("text", "").lower()).strip()
            if normalized:
                normalized_by_channel.setdefault(normalized, set()).add(channel)
        for text, channels in normalized_by_channel.items():
            if "NARRATION" in channels and "DIALOGUE" in channels:
                findings.append({"code": "CAPTION_DIALOGUE_DUPLICATION", "page_id": owner, "normalized_text": text})

        for requirement in page.get("continuity_requirements", []):
            character_id = requirement.get("character_id")
            entry = character_entries.get(character_id)
            if not entry:
                continue
            allowed_weapons = set(entry.get("authorized_weapon_ids", []))
            unknown_weapons = sorted(set(requirement.get("weapon_ids", [])) - allowed_weapons)
            if unknown_weapons:
                findings.append({"code": "UNAUTHORIZED_WEAPON", "page_id": owner, "character_id": character_id, "weapon_ids": unknown_weapons})
            allowed_forms = {item.get("manifestation_id") for item in entry.get("manifestation_rules", [])}
            if requirement.get("manifestation_id") and requirement["manifestation_id"] not in allowed_forms:
                findings.append({"code": "UNAUTHORIZED_MANIFESTATION", "page_id": owner, "character_id": character_id})

    for previous, current in zip(storyboard.get("pages", []), storyboard.get("pages", [])[1:]):
        if previous.get("continuity_out") != current.get("continuity_in"):
            findings.append({
                "code": "SCENE_CONTINUITY_MISMATCH",
                "from_page_id": previous.get("page_id"),
                "to_page_id": current.get("page_id"),
            })

    if page_numbers != list(range(1, len(page_numbers) + 1)):
        findings.append({"code": "PAGE_ORDER_NOT_CONTIGUOUS", "page_numbers": page_numbers})
    missing_events = sorted(set(required_event_ids) - covered_events)
    if missing_events:
        findings.append({"code": "STORYBOARD_EVENT_COVERAGE_INCOMPLETE", "event_ids": missing_events})
    extra_events = sorted(covered_events - set(required_event_ids))
    if extra_events:
        findings.append({"code": "STORYBOARD_USES_UNLOCKED_EVENTS", "event_ids": extra_events})
    missing_moment_placements = sorted(required_moments - covered_moments)
    if missing_moment_placements:
        findings.append({"code": "REQUIRED_MOMENTS_NOT_PLACED", "moment_ids": missing_moment_placements})
    if full_page_count < 1:
        findings.append({"code": "FULL_PAGE_IMMERSIVE_SCENE_REQUIRED"})
    return report("STORYBOARD", "FIX" if findings else "PASS", findings, storyboard.get("book_id"))


def validate_typography(spec):
    findings = _missing(spec, (
        "schema_version", "book_id", "version", "canvas", "palette", "text_channels",
        "editable_text_separate", "font_candidates", "print_readiness", "ornamental_frames",
        "text_safe_area", "page_numbering",
    ), "TYPOGRAPHY_FIELD_MISSING", spec.get("book_id"))
    if spec.get("canvas") != CANVAS:
        findings.append({"code": "TYPOGRAPHY_CANVAS_MISMATCH", "expected": CANVAS})
    if set(spec.get("palette", [])) != PALETTE:
        findings.append({"code": "PALETTE_MISMATCH", "required": sorted(PALETTE)})
    if set(spec.get("text_channels", {})) != TEXT_CHANNELS:
        findings.append({"code": "TEXT_CHANNEL_STYLE_MISSING", "required": sorted(TEXT_CHANNELS)})
    for channel, channel_spec in spec.get("text_channels", {}).items():
        if not isinstance(channel_spec, dict) or not channel_spec.get("geometry"):
            findings.append({"code": "TEXT_CHANNEL_GEOMETRY_MISSING", "channel": channel})
    if spec.get("editable_text_separate") is not True:
        findings.append({"code": "EDITABLE_TEXT_SEPARATION_REQUIRED"})
    for font in spec.get("font_candidates", []):
        if font.get("bundled") and font.get("licensing_status") != "VERIFIED_FOR_BUNDLING":
            findings.append({"code": "UNAUTHORIZED_FONT_BUNDLING", "font": font.get("name")})
        if not font.get("licensing_status") or not font.get("inspection_basis"):
            findings.append({"code": "FONT_INSPECTION_INCOMPLETE", "font": font.get("name")})
        if not font.get("bundled") and (
            font.get("licensing_status") != "NOT_VERIFIED_FOR_BUNDLING"
            or font.get("inspection_basis") != "SYSTEM_INSTALLED_REFERENCE_ONLY"
        ):
            findings.append({"code": "FONT_REFERENCE_STATUS_INVALID", "font": font.get("name")})
    readiness = spec.get("print_readiness", {})
    if readiness.get("claim") not in {"NOT_PRINT_READY", "PRINT_READY"}:
        findings.append({"code": "PRINT_READINESS_STATUS_INVALID"})
    if readiness.get("claim") == "PRINT_READY":
        missing = [item for item in ("trim", "bleed", "export_profile") if not readiness.get(item)]
        if missing:
            findings.append({"code": "PRINT_READY_CLAIM_UNSUPPORTED", "missing": missing})
    return report("TYPOGRAPHY", "FIX" if findings else "PASS", findings, spec.get("book_id"))


def validate_proof_specs(package):
    findings = _missing(package, (
        "schema_version", "book_id", "version", "manuscript_hash", "storyboard_hash",
        "provider_status", "retry_limit", "approval_policy", "approval_records", "specs",
    ), "PROOF_PACKAGE_FIELD_MISSING", package.get("book_id"))
    if package.get("retry_limit") != 2:
        findings.append({"code": "PROOF_RETRY_LIMIT_MISMATCH", "expected": 2})
    kinds = [item.get("kind") for item in package.get("specs", [])]
    if set(kinds) != PROOF_KINDS or len(kinds) != len(PROOF_KINDS):
        findings.append({"code": "PROOF_SET_INCOMPLETE", "required": sorted(PROOF_KINDS)})
    for spec in package.get("specs", []):
        owner = spec.get("id")
        findings.extend(_missing(spec, (
            "id", "kind", "title", "composition", "character_ids", "iconography",
            "setting", "style", "exclusions", "safe_regions", "source_boundaries",
            "source_support", "canvas", "review_requirements", "status", "attempts",
        ), "PROOF_SPEC_FIELD_MISSING", owner))
        if not spec.get("source_support"):
            findings.append({"code": "PROOF_SOURCE_SUPPORT_REQUIRED", "proof_id": owner})
        if spec.get("canvas") != CANVAS:
            findings.append({"code": "PROOF_CANVAS_MISMATCH", "proof_id": owner})
        findings.extend(_safe_region_findings(spec.get("safe_regions", []), owner))
        if spec.get("status") == "GENERATED":
            candidates = spec.get("attempts", [])
            if not candidates:
                findings.append({"code": "GENERATED_PROOF_HAS_NO_ATTEMPT", "proof_id": owner})
            for candidate in candidates:
                path = Path(candidate.get("image_path", ""))
                if not path.is_file():
                    findings.append({"code": "PROOF_IMAGE_MISSING", "proof_id": owner})
                elif candidate.get("image_hash") != sha256_bytes(path.read_bytes()):
                    findings.append({"code": "PROOF_IMAGE_HASH_MISMATCH", "proof_id": owner})
        elif spec.get("attempts"):
            findings.append({"code": "UNGENERATED_PROOF_HAS_ATTEMPTS", "proof_id": owner})
    if package.get("provider_status") == "BLOCKED_PROVIDER":
        if any(item.get("status") != "SPEC_READY_PROVIDER_BLOCKED" for item in package.get("specs", [])):
            findings.append({"code": "BLOCKED_PROVIDER_STATUS_INCONSISTENT"})
        if package.get("approval_records"):
            findings.append({"code": "APPROVAL_WITHOUT_RENDERED_PROOFS"})
    specs_by_id = {item.get("id"): item for item in package.get("specs", [])}
    for approval in package.get("approval_records", []):
        spec = specs_by_id.get(approval.get("proof_id"))
        if not spec:
            findings.append({"code": "APPROVAL_PROOF_ID_NOT_FOUND", "proof_id": approval.get("proof_id")})
            continue
        if approval.get("proof_spec_hash") != content_hash(spec):
            findings.append({"code": "APPROVAL_SPEC_HASH_MISMATCH", "proof_id": approval.get("proof_id")})
        if approval.get("proof_package_version") != package.get("version"):
            findings.append({"code": "APPROVAL_VERSION_MISMATCH", "proof_id": approval.get("proof_id")})
    return report("PROOF_SPECS", "FIX" if findings else "PASS", findings, package.get("book_id"))


def validate_preproduction_package(package, required_event_ids, manuscript, expected_manuscript_hash=None,
                                   required_moment_ids=None):
    findings = []
    required = ("character_bible", "location_bible", "storyboard", "typography", "proof_package")
    findings.extend(_missing(package, required, "PREPRODUCTION_COMPONENT_MISSING", package.get("book_id")))
    if findings:
        return report("VISUAL_PREPRODUCTION", "FIX", findings, package.get("book_id"))
    character = validate_character_bible(package["character_bible"])
    location = validate_location_bible(package["location_bible"])
    for component_name in ("character_bible", "location_bible", "storyboard", "typography", "proof_package"):
        if expected_manuscript_hash and package[component_name].get("manuscript_hash") != expected_manuscript_hash:
            findings.append({"code": "PREPRODUCTION_MANUSCRIPT_HASH_MISMATCH", "component": component_name})
    storyboard = validate_storyboard(
        package["storyboard"], required_event_ids, manuscript,
        package["character_bible"], package["location_bible"], expected_manuscript_hash,
        required_moment_ids,
    )
    typography = validate_typography(package["typography"])
    proofs = validate_proof_specs(package["proof_package"])
    component_reports = [character, location, storyboard, typography, proofs]
    for component in component_reports:
        findings.extend(component["findings"])
    result = "PASS" if all(item["result"] == "PASS" for item in component_reports) else "FIX"
    combined = report("VISUAL_PREPRODUCTION", result, findings, package.get("book_id"))
    combined["components"] = component_reports
    return combined


def build_semantic_visual_review_request(proof_package, provider_capability):
    """Build the honest visual-review seam; specs alone are never 'seen'."""
    image_inputs = [
        attempt for spec in proof_package.get("specs", [])
        for attempt in spec.get("attempts", []) if attempt.get("image_hash")
    ]
    available = bool(provider_capability.get("available")) and bool(image_inputs)
    request = {
        "schema_version": "1.0",
        "book_id": proof_package.get("book_id"),
        "proof_package_hash": content_hash(proof_package),
        "required_dimensions": [
            "iconographic_accuracy", "hands_and_anatomy", "character_continuity",
            "facial_consistency", "scene_correctness", "clipped_artwork",
            "lettering_readability",
        ],
        "image_inputs": image_inputs,
        "required_reviewer_kind": "visual_evaluation",
        "status": "READY_FOR_SEMANTIC_VISUAL_REVIEW" if available else "BLOCKED_PROVIDER",
        "executed": False,
        "reason": None if available else "No configured visual-evaluation backend and/or no rendered proof images.",
    }
    request["request_hash"] = content_hash(request)
    return request


class ProofStageStore:
    """Immutable proof attempts with a two-attempt cap and explicit rejection state."""

    def __init__(self, books_root, retry_limit=2):
        self.store = ProofSpecVersionStore(books_root)
        self.retry_limit = retry_limit

    def initialize(self, book_id, proof_package):
        if proof_package.get("retry_limit") != self.retry_limit:
            raise ContractError("proof package retry limit does not match store policy")
        return self.store.put(book_id, proof_package)

    def record_attempt(self, book_id, proof_id, image_path, image_hash, provider_request_id):
        current = self.store.versions(book_id)
        if not current:
            raise ContractError("proof package must be initialized before an attempt")
        payload = {**current[-1]["payload"], "specs": [dict(item) for item in current[-1]["payload"]["specs"]]}
        matches = [item for item in payload["specs"] if item.get("id") == proof_id]
        if len(matches) != 1:
            raise ContractError("proof id is not unique in the active package")
        spec = matches[0]
        attempts = list(spec.get("attempts", []))
        if len(attempts) >= self.retry_limit:
            raise ContractError("proof retry limit reached")
        path = Path(image_path)
        if not path.is_file() or sha256_bytes(path.read_bytes()) != image_hash:
            raise ContractError("proof image is missing or hash-mismatched")
        attempts.append({
            "attempt": len(attempts) + 1,
            "image_path": str(path),
            "image_hash": image_hash,
            "provider_request_id": provider_request_id,
            "decision": "AWAITING_REVIEW",
        })
        spec["attempts"] = attempts
        spec["status"] = "GENERATED"
        payload["provider_status"] = "AVAILABLE"
        return self.store.put(book_id, payload, current[-1]["content_hash"])

    def reject(self, book_id, proof_id, reviewer_id, reasons):
        current = self.store.versions(book_id)
        if not current:
            raise ContractError("proof package does not exist")
        payload = {**current[-1]["payload"], "specs": [dict(item) for item in current[-1]["payload"]["specs"]]}
        spec = next((item for item in payload["specs"] if item.get("id") == proof_id), None)
        if not spec or not spec.get("attempts"):
            raise ContractError("only a generated proof can be rejected")
        attempts = [dict(item) for item in spec["attempts"]]
        attempts[-1].update({"decision": "REJECTED", "reviewer_id": reviewer_id, "reasons": list(reasons)})
        spec["attempts"] = attempts
        spec["status"] = "REJECTED_RETRY_AVAILABLE" if len(attempts) < self.retry_limit else "REJECTED_RETRY_EXHAUSTED"
        return self.store.put(book_id, payload, current[-1]["content_hash"])
