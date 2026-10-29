"""Deterministic foundation validators and honest visual-QA tracking."""

from .util import stable_id, utc_now


RESULTS = {"PASS", "FIX", "ESCALATE"}


def report(gate, result, findings=None, subject_id=None):
    if result not in RESULTS:
        raise ValueError("invalid quality result")
    findings = findings or []
    return {
        "schema_version": "1.0",
        "id": stable_id("qa", gate, subject_id or "none", result, findings),
        "gate": gate,
        "result": result,
        "subject_id": subject_id,
        "findings": findings,
        "created_at": utc_now(),
    }


def source_event_coverage(required_event_ids, mappings, subject_id=None):
    mapped = {item.get("event_id") for item in mappings if item.get("evidence_ids")}
    missing = sorted(set(required_event_ids) - mapped)
    return report("SOURCE_EVENT_COVERAGE", "FIX" if missing else "PASS", [
        {"code": "MISSING_EVENT_EVIDENCE", "event_id": event_id} for event_id in missing
    ], subject_id)


def claim_provenance(claims, subject_id=None):
    findings = []
    for claim in claims:
        if claim.get("source_class") not in {"MULA", "SAMPRADAYA", "DRISHTI", "KALPANA"}:
            findings.append({"code": "INVALID_SOURCE_CLASS", "claim_id": claim.get("id")})
        if claim.get("source_class") in {"MULA", "SAMPRADAYA"} and not claim.get("evidence_ids"):
            findings.append({"code": "MISSING_PROVENANCE", "claim_id": claim.get("id")})
    return report("CLAIM_PROVENANCE", "FIX" if findings else "PASS", findings, subject_id)


def manuscript_completeness(manuscript, subject_id=None):
    required = ("title", "audience", "beats", "ending", "source_classification")
    missing = [field for field in required if not manuscript.get(field)]
    return report("MANUSCRIPT_COMPLETENESS", "FIX" if missing else "PASS", [
        {"code": "MISSING_FIELD", "field": field} for field in missing
    ], subject_id)


def character_iconography(records, subject_id=None):
    findings = []
    for record_item in records:
        for field in ("id", "name", "required_attributes", "prohibited_attributes", "evidence_ids"):
            if field not in record_item:
                findings.append({"code": "MISSING_ICONOGRAPHY_FIELD", "character_id": record_item.get("id"), "field": field})
    return report("CHARACTER_ICONOGRAPHY", "FIX" if findings else "PASS", findings, subject_id)


def scene_continuity(scenes, subject_id=None):
    findings = []
    for previous, current in zip(scenes, scenes[1:]):
        expected = previous.get("continuity_out", {})
        actual = current.get("continuity_in", {})
        if expected != actual:
            findings.append({"code": "CONTINUITY_MISMATCH", "from": previous.get("id"), "to": current.get("id")})
    return report("SCENE_CONTINUITY", "FIX" if findings else "PASS", findings, subject_id)


def caption_dialogue_nonduplication(pages, subject_id=None):
    findings = []
    for page in pages:
        captions = {" ".join(item.lower().split()) for item in page.get("captions", [])}
        dialogue = {" ".join(item.lower().split()) for item in page.get("dialogue", [])}
        for duplicate in sorted(captions.intersection(dialogue)):
            findings.append({"code": "DUPLICATE_CAPTION_DIALOGUE", "page_id": page.get("id"), "text": duplicate})
    return report("CAPTION_DIALOGUE", "FIX" if findings else "PASS", findings, subject_id)


def page_ordering(pages, subject_id=None):
    actual = [item.get("number") for item in pages]
    expected = list(range(1, len(pages) + 1))
    findings = [] if actual == expected else [{"code": "INVALID_PAGE_ORDER", "expected": expected, "actual": actual}]
    return report("PAGE_ORDERING", "FIX" if findings else "PASS", findings, subject_id)


def pdf_geometry_and_duplicates(pages, subject_id=None, tolerance=0.001):
    findings = []
    hashes = set()
    for page in pages:
        width, height = page.get("width"), page.get("height")
        if not width or not height or abs((float(width) / float(height)) - 0.75) > tolerance:
            findings.append({"code": "INVALID_3_4_DIMENSIONS", "page": page.get("number")})
        digest = page.get("render_sha256")
        if digest in hashes:
            findings.append({"code": "DUPLICATE_PAGE_RENDER", "page": page.get("number")})
        if digest:
            hashes.add(digest)
    return report("PDF_PREFLIGHT", "FIX" if findings else "PASS", findings, subject_id)


def visual_evaluation_status(subject_id=None):
    return report("VISUAL_EVALUATION", "ESCALATE", [{
        "code": "VISUAL_BACKEND_NOT_IMPLEMENTED",
        "message": "No image-based visual-review backend is integrated in Foundation PR2",
    }], subject_id)
