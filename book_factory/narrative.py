"""Deterministic narrative-contract validation; no prose generation."""

from .quality import report


SOURCE_CLASSES = {"MULA", "SAMPRADAYA", "DRISHTI", "KALPANA"}


def validate_manuscript(manuscript, required_event_ids=None, subject_id=None,
                        allowed_evidence_ids=None, expected_packet_hashes=None,
                        event_evidence_map=None):
    findings = []
    evidence_bound = allowed_evidence_ids is not None or expected_packet_hashes is not None
    required_fields = [
        "book_id", "version", "title", "audience", "opening", "context",
        "beats", "ending", "source_classification", "claim_map",
    ]
    if evidence_bound:
        required_fields.append("chapters")
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
    for event_id in sorted(mapped_events - set(required_event_ids or mapped_events)):
        findings.append({"code": "UNLOCKED_EVENT_USED", "event_id": event_id})

    if evidence_bound:
        coverage = manuscript.get("event_coverage", [])
        coverage_ids = [item.get("event_id") for item in coverage]
        for event_id in sorted(set(required_event_ids or []) - set(coverage_ids)):
            findings.append({"code": "EVENT_COVERAGE_RECORD_MISSING", "event_id": event_id})
        for event_id in sorted({item for item in coverage_ids if coverage_ids.count(item) > 1}):
            findings.append({"code": "DUPLICATE_EVENT_COVERAGE", "event_id": event_id})
        chapter_ids = {chapter.get("id") for chapter in manuscript.get("chapters", [])}
        for item in coverage:
            if not item.get("chapter_ids") or not set(item.get("chapter_ids", [])).issubset(chapter_ids):
                findings.append({"code": "INVALID_EVENT_CHAPTER_COVERAGE", "event_id": item.get("event_id")})

    expected_packets = sorted(expected_packet_hashes or [])
    actual_packets = sorted(manuscript.get("source_packet_hashes", []))
    if expected_packets and actual_packets != expected_packets:
        findings.append({"code": "SOURCE_PACKET_HASH_MISMATCH", "expected": expected_packets, "actual": actual_packets})

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
        if evidence_bound and source_class in {"MULA", "SAMPRADAYA"}:
            if claim.get("event_id") not in set(required_event_ids or []):
                findings.append({"code": "CANONICAL_CLAIM_EVENT_NOT_LOCKED", "claim_id": claim_id, "event_id": claim.get("event_id")})
            allowed = (
                set(allowed_evidence_ids)
                if allowed_evidence_ids is not None
                else set(claim.get("evidence_ids", []))
            )
            unknown = sorted(set(claim.get("evidence_ids", [])) - allowed)
            if unknown:
                findings.append({"code": "UNKNOWN_EVIDENCE_REFERENCE", "claim_id": claim_id, "evidence_ids": unknown})
            if event_evidence_map is not None and claim.get("event_id") in event_evidence_map:
                wrong_event_evidence = sorted(
                    set(claim.get("evidence_ids", [])) - set(event_evidence_map[claim["event_id"]])
                )
                if wrong_event_evidence:
                    findings.append({
                        "code": "EVIDENCE_OUTSIDE_CLAIM_EVENT",
                        "claim_id": claim_id,
                        "event_id": claim.get("event_id"),
                        "evidence_ids": wrong_event_evidence,
                    })

    for dialogue in manuscript.get("dialogue", []):
        if dialogue.get("verbatim_source_quote") and not dialogue.get("evidence_ids"):
            findings.append({"code": "UNATTRIBUTED_SOURCE_QUOTE", "dialogue_id": dialogue.get("id")})
        if not dialogue.get("speaker_id"):
            findings.append({"code": "DIALOGUE_SPEAKER_MISSING", "dialogue_id": dialogue.get("id")})
    if manuscript.get("next_book_hook") and not manuscript.get("ending_before_next_book_hook"):
        findings.append({"code": "ENDING_NOT_COMPLETE_BEFORE_HOOK"})
    if evidence_bound:
        if not manuscript.get("complete_narrative"):
            findings.append({"code": "MANUSCRIPT_NOT_MARKED_COMPLETE"})
        creator = manuscript.get("creator", {})
        if not creator.get("id") or creator.get("capability") != "manuscript_generation":
            findings.append({"code": "MANUSCRIPT_CREATOR_CAPABILITY_MISSING"})
    return report("MANUSCRIPT_CONTRACT", "FIX" if findings else "PASS", findings, subject_id or manuscript.get("book_id"))
