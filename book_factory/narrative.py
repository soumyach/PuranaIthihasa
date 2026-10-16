"""Deterministic narrative-contract validation; no prose generation."""

from .quality import report


SOURCE_CLASSES = {"MULA", "SAMPRADAYA", "DRISHTI", "KALPANA"}


def validate_manuscript(manuscript, required_event_ids=None, subject_id=None):
    findings = []
    required_fields = (
        "book_id", "version", "title", "audience", "opening", "context",
        "beats", "ending", "source_classification", "claim_map",
    )
    for field in required_fields:
        if not manuscript.get(field):
            findings.append({"code": "MISSING_MANUSCRIPT_FIELD", "field": field})

    mapped_events = set()
    beat_ids = set()
    for beat in manuscript.get("beats", []):
        beat_id = beat.get("id")
        if not beat_id:
            findings.append({"code": "BEAT_ID_MISSING"})
            continue
        if beat_id in beat_ids:
            findings.append({"code": "DUPLICATE_BEAT_ID", "beat_id": beat_id})
        beat_ids.add(beat_id)
        mapped_events.update(beat.get("event_ids", []))
    for event_id in sorted(set(required_event_ids or []) - mapped_events):
        findings.append({"code": "MISSING_REQUIRED_EVENT", "event_id": event_id})

    for claim in manuscript.get("claim_map", []):
        claim_id = claim.get("id")
        source_class = claim.get("source_class")
        if source_class not in SOURCE_CLASSES:
            findings.append({"code": "INVALID_SOURCE_CLASS", "claim_id": claim_id})
        elif source_class in {"MULA", "SAMPRADAYA"} and not claim.get("evidence_ids"):
            findings.append({"code": "UNSUPPORTED_SOURCE_CLAIM", "claim_id": claim_id})
        elif source_class in {"DRISHTI", "KALPANA"} and not claim.get("adaptation_note"):
            findings.append({"code": "UNLABELED_ADAPTATION", "claim_id": claim_id})
        if claim.get("beat_id") not in beat_ids:
            findings.append({"code": "CLAIM_BEAT_NOT_FOUND", "claim_id": claim_id, "beat_id": claim.get("beat_id")})

    for dialogue in manuscript.get("dialogue", []):
        if dialogue.get("verbatim_source_quote") and not dialogue.get("evidence_ids"):
            findings.append({"code": "UNATTRIBUTED_SOURCE_QUOTE", "dialogue_id": dialogue.get("id")})
        if not dialogue.get("speaker_id"):
            findings.append({"code": "DIALOGUE_SPEAKER_MISSING", "dialogue_id": dialogue.get("id")})
    if manuscript.get("next_book_hook") and not manuscript.get("ending_before_next_book_hook"):
        findings.append({"code": "ENDING_NOT_COMPLETE_BEFORE_HOOK"})
    return report("MANUSCRIPT_CONTRACT", "FIX" if findings else "PASS", findings, subject_id or manuscript.get("book_id"))
