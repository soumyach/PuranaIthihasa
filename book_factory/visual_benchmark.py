"""PR7 Visual Gold Standard, comparison, and proof-recovery controls."""

import json
from collections import Counter
from copy import deepcopy
from pathlib import Path

from .errors import ContractError
from .illustration_production import ProofExecutionLedger, inspect_png
from .source_graph import ReadOnlySourceGraph
from .util import content_hash, load_json, sha256_bytes
from .versioning import (
    CharacterBibleVersionStore,
    CharacterReferenceVersionStore,
    LocationBibleVersionStore,
    ManuscriptVersionStore,
    ProofRecoveryRequestVersionStore,
    ProofSpecVersionStore,
    StoryboardVersionStore,
)


GOLD_CATEGORIES = {
    "A_COVER_AND_SERIES_IDENTITY",
    "B_INTIMATE_CONVERSATION",
    "C_HUMAN_EMOTIONAL_INTERACTION",
    "D_TRADITIONAL_INDIAN_SETTING",
    "E_DIVINE_MANIFESTATION",
    "F_LARGE_SCALE_BATTLE",
    "G_SEQUENTIAL_COMIC_STORYTELLING",
    "H_CINEMATIC_REVEAL_OR_IMMERSIVE_COMPOSITION",
}
REFERENCE_ROLES = {
    "REFERENCE_A_SERIES_VISUAL_IDENTITY",
    "REFERENCE_B_PAGE_COMPOSITION",
    "REFERENCE_C_CHARACTER_IDENTITY",
    "REFERENCE_D_SETTING_ENVIRONMENT",
}
COMPARATIVE_DIMENSIONS = (
    "SOURCE_FIDELITY",
    "RELIGIOUS_ICONOGRAPHY",
    "CULTURAL_AUTHENTICITY",
    "CHARACTER_CONTINUITY",
    "NARRATIVE_SPECIFICITY",
    "COMPOSITION",
    "EMOTIONAL_EXPRESSIVENESS",
    "VISUAL_REFERENCE_ALIGNMENT",
    "PAGE_DESIGN_COMPATIBILITY",
    "ANATOMY",
    "LETTERING_READINESS",
)
PRODUCTION_UNITS = {"CHARACTER_REFERENCE", "PANEL_ILLUSTRATION", "FULL_PAGE_IMMERSIVE"}
RECOVERY_RECOMMENDATIONS = {"REUSE", "LOCAL_EDIT", "REGENERATE", "ESCALATE"}
EXPECTED_PROOFS = {
    "dm04-proof-quiet-conversation",
    "dm04-proof-divine-reveal",
    "dm04-proof-battle",
    "dm04-proof-full-page",
}
EXPECTED_PRODUCTION_UNITS = {
    "dm04-proof-quiet-conversation": "PANEL_ILLUSTRATION",
    "dm04-proof-divine-reveal": "FULL_PAGE_IMMERSIVE",
    "dm04-proof-battle": "PANEL_ILLUSTRATION",
    "dm04-proof-full-page": "FULL_PAGE_IMMERSIVE",
}


def _file_hash(path):
    return sha256_bytes(Path(path).read_bytes())


def _require_exact_file(root, relative_path, digest, size=None):
    path = Path(root) / relative_path
    if not path.is_file():
        raise ContractError("required PR7 asset is missing", {"path": relative_path})
    actual = _file_hash(path)
    if actual != digest:
        raise ContractError("PR7 asset hash mismatch", {
            "path": relative_path, "expected": digest, "actual": actual,
        })
    if size is not None and path.stat().st_size != size:
        raise ContractError("PR7 asset byte-size mismatch", {"path": relative_path})
    return path


def validate_gold_standard(root, require_source_assets=False):
    root = Path(root)
    manifest_path = root / "book-factory" / "references" / "visual-gold-standard" / "manifest.json"
    manifest = load_json(manifest_path)
    pages = manifest.get("pages", [])
    if len(pages) != 8:
        raise ContractError("Visual Gold Standard must contain exactly eight curated pages")
    reference_ids = [item.get("reference_id") for item in pages]
    if len(reference_ids) != len(set(reference_ids)):
        raise ContractError("Visual Gold Standard reference IDs must be unique")
    if set(manifest.get("coverage", {})) != GOLD_CATEGORIES:
        raise ContractError("Visual Gold Standard category coverage is incomplete")
    for category, identifiers in manifest["coverage"].items():
        if not identifiers or set(identifiers) - set(reference_ids):
            raise ContractError("Visual Gold Standard category has invalid page bindings", {"category": category})
    assets = {item["asset_id"]: item for item in manifest.get("source_assets", [])}
    if len(assets) != 2:
        raise ContractError("Visual Gold Standard requires the two registered benchmark PDFs")
    source_results = []
    for asset in assets.values():
        source_path = root / asset["path"]
        if not source_path.is_file():
            if require_source_assets:
                raise ContractError("benchmark PDF is unavailable", {"path": asset["path"]})
            source_results.append({"asset_id": asset["asset_id"], "status": "MISSING_LOCAL_REFERENCE"})
            continue
        _require_exact_file(root, asset["path"], asset["sha256"], asset["bytes"])
        source_results.append({"asset_id": asset["asset_id"], "status": "VERIFIED"})
    page_results = []
    for page in pages:
        asset = assets.get(page.get("source_asset_id"))
        if not asset or page.get("reference_asset_hash") != asset["sha256"]:
            raise ContractError("curated page does not bind its exact source PDF", {"reference_id": page.get("reference_id")})
        path = _require_exact_file(
            root, page["extracted_path"], page["extracted_sha256"], page["bytes"]
        )
        image = inspect_png(path)
        if (image["width"], image["height"]) != (page["width"], page["height"]):
            raise ContractError("curated page dimensions do not match manifest", {"reference_id": page["reference_id"]})
        required_page_fields = {
            "selection_reason", "qualities_to_preserve", "composition_principles",
            "color_characteristics", "expression_qualities", "storytelling_characteristics",
            "lettering_approach", "cultural_iconographic_constraints",
            "known_shortcomings_not_to_copy", "applicable_future_scene_types",
        }
        if any(not page.get(field) for field in required_page_fields):
            raise ContractError("curated page analysis is incomplete", {"reference_id": page["reference_id"]})
        if set(page.get("selected_for", [])) - GOLD_CATEGORIES:
            raise ContractError("curated page has unknown coverage category", {"reference_id": page["reference_id"]})
        page_results.append({
            "reference_id": page["reference_id"],
            "sha256": image["sha256"],
            "width": image["width"],
            "height": image["height"],
        })
    return {
        "status": "PASS",
        "manifest_hash": content_hash(manifest),
        "pages": page_results,
        "source_assets": source_results,
    }


def validate_cultural_authenticity(root):
    root = Path(root)
    policy = load_json(root / "book-factory" / "policies" / "indian-cultural-authenticity.json")
    expected_decisions = {
        "SOURCE_REQUIRED", "TRADITION_SUPPORTED", "ARTISTICALLY_APPROVED",
        "SOURCE_SILENT", "FORBIDDEN",
    }
    if set(policy.get("decision_values", [])) != expected_decisions:
        raise ContractError("cultural-authenticity evidence decisions are incomplete")
    labels = " ".join(item.get("label", "").lower() for item in policy.get("explicit_foreign_style_exclusions", []))
    required_terms = ("corinthian", "roman", "trojan", "spartan", "medieval", "viking", "western fantasy", "rpg", "flag", "castle")
    if any(term not in labels for term in required_terms):
        raise ContractError("foreign-style exclusion list is incomplete")
    failures = {item["failure_id"]: item for item in policy.get("dm04_specific_failures", [])}
    for failure_id in ("dm04-pr6-greco-roman-red-crest", "dm04-pr6-unsupported-demonic-face-flag"):
        if failures.get(failure_id, {}).get("decision") != "FORBIDDEN":
            raise ContractError("explicit PR6 cultural-authenticity failure is not prohibited", {"failure_id": failure_id})
    return {"status": "PASS", "policy_hash": content_hash(policy), "subject_gates": len(policy["subject_gates"])}


def _expected_pr6_images(root):
    root = Path(root)
    receipts = [
        load_json(path) for path in sorted((root / "books" / "DM04" / "illustration-proofs" / "receipts").glob("*.json"))
    ]
    return {item["image"]["sha256"]: item["image"]["path"] for item in receipts}


def validate_comparison(root):
    root = Path(root)
    path = root / "books" / "DM04" / "visual-comparisons" / "pr7-comparison.json"
    report = load_json(path)
    if report.get("book_id") != "DM04" or report.get("actual_pixels_inspected") is not True:
        raise ContractError("PR7 comparison must attest actual DM04 pixel inspection")
    reviewer = report.get("reviewer", {})
    if not reviewer.get("image_capable") or not reviewer.get("independent_from_pr6_producer"):
        raise ContractError("PR7 comparison requires an independent image-capable reviewer")
    if reviewer.get("id") == reviewer.get("pr6_producer_id"):
        raise ContractError("PR7 comparison reviewer cannot be the PR6 producer")
    gold = validate_gold_standard(root)
    gold_ids = {item["reference_id"] for item in gold["pages"]}
    side = report.get("side_by_side", {})
    _require_exact_file(root, side["path"], side["sha256"], side["bytes"])
    expected_images = _expected_pr6_images(root)
    records = report.get("records", [])
    if len(records) != 8 or Counter(item.get("proof_id") for item in records) != Counter({proof: 2 for proof in EXPECTED_PROOFS}):
        raise ContractError("PR7 comparison must cover both attempts for all four proofs")
    observed = set()
    for record in records:
        if record.get("overall") not in {"PASS", "FIX", "ESCALATE"}:
            raise ContractError("comparison record lacks a valid overall result", {"proof_id": record.get("proof_id")})
        digest = record.get("image_sha256")
        if digest not in expected_images or expected_images[digest] != record.get("image_path"):
            raise ContractError("comparison image is not bound to a PR6 receipt", {"image_hash": digest})
        _require_exact_file(root, record["image_path"], digest)
        observed.add(digest)
        if not record.get("gold_reference_ids") or set(record["gold_reference_ids"]) - gold_ids:
            raise ContractError("comparison has an invalid Gold Standard binding", {"image_hash": digest})
        assessments = record.get("dimensions", [])
        if tuple(item.get("dimension") for item in assessments) != COMPARATIVE_DIMENSIONS:
            raise ContractError("comparison dimensions are missing or out of contract order", {"image_hash": digest})
        for assessment in assessments:
            if assessment.get("result") not in {"PASS", "FIX", "ESCALATE"} or not assessment.get("evidence"):
                raise ContractError("comparison dimension lacks result or pixel evidence", {"image_hash": digest})
            if assessment["result"] != "PASS" and not assessment.get("corrective_guidance"):
                raise ContractError("failed comparison dimension lacks corrective guidance", {"image_hash": digest})
    if observed != set(expected_images):
        raise ContractError("comparison does not bind all eight exact PR6 images")
    battle_one = next(item for item in records if item["proof_id"] == "dm04-proof-battle" and item["attempt_number"] == 1)
    cultural = next(item for item in battle_one["dimensions"] if item["dimension"] == "CULTURAL_AUTHENTICITY")
    combined = (cultural["evidence"] + " " + cultural["corrective_guidance"]).lower()
    if "greco-roman" not in combined or "demonic-face" not in combined:
        raise ContractError("battle comparison omits the two explicit PR6 authenticity failures")
    return {
        "status": "PASS",
        "comparison_hash": content_hash(report),
        "records": len(records),
        "side_by_side_hash": side["sha256"],
    }


def _locked_component_hashes(root):
    root = Path(root)
    books = root / "books"
    dossiers = [load_json(path) for path in sorted((books / "DM04" / "source-readiness").glob("*.json"))]
    packets = [load_json(path) for path in sorted((books / "DM04" / "story-packets").glob("*.json"))]
    if len(dossiers) != 1 or len(packets) != 1:
        raise ContractError("PR7 requires one locked DM04 dossier and Story Packet")
    return {
        "manuscript": ManuscriptVersionStore(books).versions("DM04")[-1]["content_hash"],
        "source_dossier": dossiers[0]["dossier_hash"],
        "story_packet": packets[0]["packet_hash"],
        "storyboard": StoryboardVersionStore(books).versions("DM04")[-1]["content_hash"],
        "character_bible": CharacterBibleVersionStore(books).versions("DM04")[-1]["content_hash"],
        "location_bible": LocationBibleVersionStore(books).versions("DM04")[-1]["content_hash"],
        "proof_package": ProofSpecVersionStore(books).versions("DM04")[-1]["content_hash"],
        "character_registry": CharacterReferenceVersionStore(books).versions("DM04")[-1]["payload"]["registry_hash"],
        "rules": _file_hash(root / "MYTHOLOGY_COMIC_RULES.md"),
        "source_graph": ReadOnlySourceGraph(root / "research" / "source-graph").verify()["graph_hash"],
    }


def _validate_recovery_payload(root, payload):
    root = Path(root)
    if payload.get("book_id") != "DM04" or payload.get("generation_authorized") is not False:
        raise ContractError("PR7 recovery payload must be non-executable DM04 preparation")
    if payload.get("execution_milestone") != "PR8_IF_SEPARATELY_AUTHORIZED":
        raise ContractError("recovery payload must defer execution to a separately authorized PR8")
    history = payload.get("pr6_history", {})
    if history.get("counter_reset") is not False or history.get("retry_ceiling_exhausted") is not True:
        raise ContractError("PR6 retry exhaustion must persist")
    ledger_events = ProofExecutionLedger(root / "books", "DM04").events()
    intents = [item for item in ledger_events if item.get("status") == "INTENT_RECORDED"]
    successes = [item for item in ledger_events if item.get("status") == "SUCCEEDED"]
    counts = Counter(item["proof_id"] for item in intents)
    if len(intents) != 8 or len(successes) != 8 or counts != Counter({proof: 2 for proof in EXPECTED_PROOFS}):
        raise ContractError("PR6 proof ledger no longer reflects the exhausted 2x4 attempt history")
    current_hashes = _locked_component_hashes(root)
    for name, digest in current_hashes.items():
        if payload.get("locked_hashes", {}).get(name) != digest:
            raise ContractError("recovery request has a stale locked hash", {"component": name})
    gold_manifest = load_json(root / "book-factory" / "references" / "visual-gold-standard" / "manifest.json")
    gold = {item["reference_id"]: item for item in gold_manifest["pages"]}
    requests = payload.get("requests", [])
    if len(requests) != 4 or {item.get("proof_id") for item in requests} != EXPECTED_PROOFS:
        raise ContractError("PR7 must prepare exactly four DM04 recovery requests")
    if len({item.get("recovery_request_id") for item in requests}) != 4:
        raise ContractError("recovery request IDs must be stable and unique")
    latest_reviews = {}
    for path in sorted((root / "books" / "DM04" / "visual-reviews").glob("v*.json")):
        review = load_json(path)["payload"]
        latest_reviews[review["proof_id"]] = review
    proof_specs = {
        item["id"]: item
        for item in ProofSpecVersionStore(root / "books").versions("DM04")[-1]["payload"]["specs"]
    }
    for request in requests:
        proof_id = request["proof_id"]
        if request.get("recommendation") not in RECOVERY_RECOMMENDATIONS:
            raise ContractError("invalid recovery recommendation", {"proof_id": proof_id})
        if request.get("production_unit") != EXPECTED_PRODUCTION_UNITS[proof_id]:
            raise ContractError("recovery request has wrong visual production unit", {"proof_id": proof_id})
        if request.get("review_checklist") != list(COMPARATIVE_DIMENSIONS):
            raise ContractError("recovery review checklist is incomplete", {"proof_id": proof_id})
        if not request.get("principal_action") or not request.get("concise_prompt"):
            raise ContractError("recovery request is not scene-specific", {"proof_id": proof_id})
        if len(request.get("concise_prompt", "")) > 1800:
            raise ContractError("recovery prompt is not concise", {"proof_id": proof_id})
        script_path = _require_exact_file(root, request["page_script_path"], request["page_script_sha256"])
        page_script = load_json(script_path)
        if (
            request.get("page_id") != page_script.get("page_id")
            or request.get("panel_id") not in {item["id"] for item in page_script.get("panels", [])}
            or request.get("event_ids") != page_script.get("event_ids")
        ):
            raise ContractError("recovery request has stale page or panel binding", {"proof_id": proof_id})
        proof_spec = proof_specs.get(proof_id)
        if not proof_spec or request.get("proof_spec_hash") != content_hash(proof_spec):
            raise ContractError("recovery request has a stale proof-spec hash", {"proof_id": proof_id})
        parent = request.get("parent_pr6", {})
        review = latest_reviews.get(proof_id, {})
        if parent.get("attempts_used") != 2 or parent.get("image_hash") != review.get("image", {}).get("sha256") or parent.get("review_hash") != review.get("review_hash"):
            raise ContractError("recovery request is not parent-linked to latest PR6 evidence", {"proof_id": proof_id})
        roles = request.get("reference_package", [])
        if len(roles) != 4 or {item.get("role") for item in roles} != REFERENCE_ROLES:
            raise ContractError("recovery request must distinguish all four reference roles", {"proof_id": proof_id})
        by_role = {item["role"]: item for item in roles}
        for required in ("REFERENCE_A_SERIES_VISUAL_IDENTITY", "REFERENCE_B_PAGE_COMPOSITION"):
            reference = by_role[required]
            gold_page = gold.get(reference.get("reference_id"))
            if not gold_page or reference.get("path") != gold_page["extracted_path"] or reference.get("sha256") != gold_page["extracted_sha256"]:
                raise ContractError("required Gold Standard reference binding is invalid", {"proof_id": proof_id, "role": required})
        for reference in roles:
            if reference.get("reference_id"):
                gold_page = gold.get(reference["reference_id"])
                if not gold_page or reference.get("path") != gold_page["extracted_path"] or reference.get("sha256") != gold_page["extracted_sha256"]:
                    raise ContractError("recovery reference hash or path is invalid", {"proof_id": proof_id, "role": reference["role"]})
            if reference["role"] in {"REFERENCE_A_SERIES_VISUAL_IDENTITY", "REFERENCE_B_PAGE_COMPOSITION"} and reference.get("content_transfer") != "FORBIDDEN":
                raise ContractError("style and composition references must forbid story-content transfer", {"proof_id": proof_id})
        if by_role["REFERENCE_C_CHARACTER_IDENTITY"].get("path") is not None:
            raise ContractError("no rejected PR6 image may become an approved character reference", {"proof_id": proof_id})
        if not request.get("character_references") or any(
            item.get("image_status") != "UNAVAILABLE_NO_HUMAN_APPROVED_EXACT_ASSET"
            for item in request["character_references"]
        ):
            raise ContractError("character-reference availability is misrepresented", {"proof_id": proof_id})
        if not request.get("cultural_authenticity_constraints") or not request.get("source_iconography_constraints"):
            raise ContractError("recovery request lacks cultural or iconographic constraints", {"proof_id": proof_id})
        if not request.get("prohibited_transfers"):
            raise ContractError("recovery request lacks forbidden content transfers", {"proof_id": proof_id})
        lettering = request.get("lettering_strategy", {})
        if lettering.get("artwork_contains_text") is not False or not lettering.get("geometry_key"):
            raise ContractError("recovery request lacks deterministic lettering separation", {"proof_id": proof_id})
    prohibited = " ".join(
        transfer.lower()
        for request in requests
        for transfer in request.get("prohibited_transfers", [])
    )
    for identity in ("vishnu", "narada", "raktabija", "seven mothers"):
        if identity not in prohibited:
            raise ContractError("recovery package omits an explicit benchmark content exclusion", {"identity": identity})
    budget = payload.get("recommended_pr8_budget", {})
    if budget.get("authorization_status") != "NOT_AUTHORIZED" or budget.get("maximum_total_image_operations") != 4:
        raise ContractError("PR8 budget must remain a four-operation unapproved recommendation")
    if budget.get("paid_calls_enabled") is not False or budget.get("maximum_paid_spend_minor_units") != 0:
        raise ContractError("PR7 cannot authorize paid recovery work")
    return payload


def build_recovery_payload(root, book_id):
    if book_id == "DM08":
        raise ContractError("DM08 is an immutable EXISTING_EDITION and cannot enter proof recovery")
    if book_id != "DM04":
        raise ContractError("PR7 recovery preparation is locked to DM04")
    root = Path(root)
    payload = deepcopy(load_json(root / "book-factory" / "config" / "pr7-dm04-recovery-blueprint.json"))
    for request in payload["requests"]:
        request["campaign_id"] = payload["campaign_id"]
        request["generation_authorized"] = False
        request["recovery_operation_number"] = 1
        request["pr6_attempts_preserved"] = 2
        unsigned = {key: value for key, value in request.items() if key != "request_hash"}
        request["request_hash"] = content_hash(unsigned)
    payload["request_count"] = len(payload["requests"])
    payload["campaign_hash"] = content_hash({key: value for key, value in payload.items() if key != "campaign_hash"})
    return _validate_recovery_payload(root, payload)


def prepare_recovery_requests(root, book_id):
    root = Path(root)
    payload = build_recovery_payload(root, book_id)
    store = ProofRecoveryRequestVersionStore(root / "books")
    current = store.versions(book_id)
    if current and current[-1]["payload"] == payload:
        record = current[-1]
    else:
        parent_hash = current[-1]["content_hash"] if current else None
        record = store.put(book_id, payload, parent_hash=parent_hash)
    return {
        "status": "RECOVERY_REQUESTS_PREPARED_GENERATION_NOT_AUTHORIZED",
        "book_id": book_id,
        "request_count": len(payload["requests"]),
        "campaign_hash": payload["campaign_hash"],
        "version_hash": record["content_hash"],
        "version": record["version"],
        "path": str(root / "books" / book_id / "proof-recovery-requests" / ("v%04d.json" % record["version"])),
    }


def validate_recovery_requests(root):
    root = Path(root)
    expected = build_recovery_payload(root, "DM04")
    versions = ProofRecoveryRequestVersionStore(root / "books").versions("DM04")
    if len(versions) != 1:
        raise ContractError("PR7 requires exactly one immutable recovery-request version")
    if versions[0]["payload"] != expected:
        raise ContractError("stored PR7 recovery requests do not match locked evidence")
    return {
        "status": "PASS",
        "requests": len(expected["requests"]),
        "campaign_hash": expected["campaign_hash"],
        "version_hash": versions[0]["content_hash"],
        "generation_authorized": False,
    }


def validate_lettering_and_units(root):
    root = Path(root)
    units = load_json(root / "book-factory" / "contracts" / "visual-production-units.json")
    if {item.get("type") for item in units.get("units", [])} != PRODUCTION_UNITS:
        raise ContractError("visual production unit contract is incomplete")
    lettering = load_json(root / "book-factory" / "contracts" / "lettering-composition.json")
    geometry = lettering.get("dm04_recovery_geometry", {})
    expected = {"page-1-panel-2", "page-4-full", "page-17-panel-1", "page-29-full"}
    if set(geometry) != expected:
        raise ContractError("DM04 recovery lettering geometry is incomplete")
    for key, item in geometry.items():
        panel = item.get("panel", {})
        values = [panel.get(name) for name in ("x", "y", "width", "height")]
        if any(not isinstance(value, (int, float)) for value in values) or any(value < 0 or value > 1 for value in values):
            raise ContractError("lettering geometry is outside normalized canvas", {"geometry": key})
        if panel["x"] + panel["width"] > 1 or panel["y"] + panel["height"] > 1:
            raise ContractError("panel geometry exceeds page bounds", {"geometry": key})
        for text in item.get("text", []):
            box = [text.get(name) for name in ("x", "y", "width", "height")]
            if any(not isinstance(value, (int, float)) for value in box) or text["x"] + text["width"] > 1 or text["y"] + text["height"] > 1:
                raise ContractError("text geometry exceeds page bounds", {"geometry": key})
    return {"status": "PASS", "production_units": len(units["units"]), "geometry_records": len(geometry)}


def validate_pr7(root, require_source_assets=False):
    root = Path(root)
    return {
        "status": "PASS",
        "gold_standard": validate_gold_standard(root, require_source_assets=require_source_assets),
        "cultural_authenticity": validate_cultural_authenticity(root),
        "comparison": validate_comparison(root),
        "recovery_requests": validate_recovery_requests(root),
        "lettering_and_units": validate_lettering_and_units(root),
        "generation_executed": False,
    }
