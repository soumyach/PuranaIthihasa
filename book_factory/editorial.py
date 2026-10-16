"""Independent editorial gate aggregation with hash-bound agent evidence."""

from .narrative import validate_manuscript
from .quality import report
from .util import content_hash, stable_id


REQUIRED_SEMANTIC_DIMENSIONS = {
    "complete_source_event_coverage",
    "factual_and_theological_accuracy",
    "character_and_divine_identity_accuracy",
    "causal_sequence",
    "framing_and_background",
    "family_readability",
    "dialogue_and_emotional_progression",
    "action_narration_reflection_balance",
    "quotation_and_source_notes",
    "ending",
    "collection_continuity",
}


def editorial_review(manuscript, required_event_ids=None, reviewer=None,
                     manuscript_hash=None, packet_hashes=None,
                     allowed_evidence_ids=None, event_evidence_map=None):
    reviewer = reviewer or {}
    # An unverified semantic response can never be converted into a deterministic
    # FIX and thereby appear to have participated in review.
    if reviewer and (
        reviewer.get("id") == manuscript.get("creator", {}).get("id")
        or not reviewer.get("independent")
        or not reviewer.get("capability_verified")
        or reviewer.get("provider_kind") != "editorial_review"
    ):
        return report(
            "EDITORIAL_INDEPENDENT_QA",
            "ESCALATE",
            [{"code": "REVIEWER_NOT_INDEPENDENT", "reviewer_id": reviewer.get("id")}],
            manuscript.get("book_id"),
        )
    if not reviewer:
        return report(
            "EDITORIAL_INDEPENDENT_QA",
            "ESCALATE",
            [{"code": "INDEPENDENT_SEMANTIC_REVIEW_REQUIRED"}],
            manuscript.get("book_id"),
        )
    deterministic = validate_manuscript(
        manuscript,
        required_event_ids,
        allowed_evidence_ids=allowed_evidence_ids,
        expected_packet_hashes=packet_hashes,
        event_evidence_map=event_evidence_map,
    )
    findings = list(deterministic["findings"])
    if deterministic["result"] == "FIX":
        return report("EDITORIAL_INDEPENDENT_QA", "FIX", findings, manuscript.get("book_id"))
    if (
        reviewer.get("id") == manuscript.get("creator", {}).get("id")
        or not reviewer.get("independent")
        or not reviewer.get("capability_verified")
        or reviewer.get("provider_kind") != "editorial_review"
    ):
        findings.append({"code": "REVIEWER_NOT_INDEPENDENT", "reviewer_id": reviewer.get("id")})
        return report("EDITORIAL_INDEPENDENT_QA", "ESCALATE", findings, manuscript.get("book_id"))
    if not reviewer.get("reviewed_manuscript_hash") or not reviewer.get("reviewed_packet_hashes"):
        findings.append({"code": "REVIEW_INPUT_HASH_ATTESTATION_MISSING"})
        return report("EDITORIAL_INDEPENDENT_QA", "ESCALATE", findings, manuscript.get("book_id"))
    if manuscript_hash and reviewer.get("reviewed_manuscript_hash") != manuscript_hash:
        findings.append({"code": "REVIEWED_MANUSCRIPT_HASH_MISMATCH"})
        return report("EDITORIAL_INDEPENDENT_QA", "ESCALATE", findings, manuscript.get("book_id"))
    if packet_hashes and sorted(reviewer.get("reviewed_packet_hashes", [])) != sorted(packet_hashes):
        findings.append({"code": "REVIEWED_PACKET_HASH_MISMATCH"})
        return report("EDITORIAL_INDEPENDENT_QA", "ESCALATE", findings, manuscript.get("book_id"))
    missing = sorted(REQUIRED_SEMANTIC_DIMENSIONS - set(reviewer.get("reviewed_dimensions", [])))
    if missing:
        findings.append({"code": "SEMANTIC_DIMENSIONS_NOT_REVIEWED", "dimensions": missing})
        return report("EDITORIAL_INDEPENDENT_QA", "ESCALATE", findings, manuscript.get("book_id"))
    result = reviewer.get("result")
    if result not in {"PASS", "FIX", "ESCALATE"}:
        findings.append({"code": "INVALID_REVIEW_RESULT"})
        result = "ESCALATE"
    if result == "PASS":
        assessments = reviewer.get("dimension_assessments", [])
        assessed_dimensions = [item.get("dimension") for item in assessments]
        if (
            set(assessed_dimensions) != REQUIRED_SEMANTIC_DIMENSIONS
            or len(assessed_dimensions) != len(REQUIRED_SEMANTIC_DIMENSIONS)
            or any(item.get("result") != "PASS" for item in assessments)
        ):
            findings.append({"code": "SEMANTIC_PASS_ASSESSMENTS_INCOMPLETE"})
            result = "ESCALATE"
        checked_events = {
            item.get("event_id")
            for item in reviewer.get("evidence_checks", [])
            if item.get("kind") == "SOURCE_EVENT_CHECK" and item.get("result") == "PASS"
        }
        missing_event_checks = sorted(set(required_event_ids or []) - checked_events)
        if missing_event_checks:
            findings.append({"code": "SEMANTIC_PASS_EVENT_CHECKS_INCOMPLETE", "event_ids": missing_event_checks})
            result = "ESCALATE"
    findings.extend(reviewer.get("findings", []))
    return report("EDITORIAL_INDEPENDENT_QA", result, findings, manuscript.get("book_id"))


def finalize_review(book_id, reviewer_payload, deterministic_report, execution):
    """Create the immutable semantic review payload stored by the version store."""
    record = {
        "schema_version": "1.0",
        "book_id": book_id,
        "reviewer": {
            "id": execution["agent_id"],
            "role": execution.get("role", "family-editor"),
            "provider_kind": "editorial_review",
            "capability_verified": True,
            "independent": True,
            "execution_mechanism": execution["mechanism"],
            "attestation_scope": execution["attestation_scope"],
        },
        "reviewed_manuscript_hash": reviewer_payload["reviewed_manuscript_hash"],
        "reviewed_packet_hashes": sorted(reviewer_payload["reviewed_packet_hashes"]),
        "reviewed_dimensions": sorted(reviewer_payload["reviewed_dimensions"]),
        "result": deterministic_report["result"],
        "findings": deterministic_report["findings"],
        "dimension_assessments": reviewer_payload.get("dimension_assessments", []),
        "evidence_checks": reviewer_payload.get("evidence_checks", []),
        "limitations": reviewer_payload.get("limitations", []),
        "certification_scope": "INDEPENDENT_MANUSCRIPT_EDITORIAL_REVIEW_ONLY",
        "publication_readiness_certified": False,
        "source_readiness_overridden": False,
    }
    record["review_hash"] = content_hash(record)
    record["id"] = stable_id("editorial-review", book_id, record["review_hash"])
    return record
