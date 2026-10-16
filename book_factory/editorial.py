"""Independent editorial gate aggregation with honest semantic escalation."""

from .narrative import validate_manuscript
from .quality import report


REQUIRED_SEMANTIC_DIMENSIONS = {
    "clarity", "pacing", "age_suitability", "dignity", "identity_distinctness", "source_fidelity"
}


def editorial_review(manuscript, required_event_ids=None, reviewer=None):
    deterministic = validate_manuscript(manuscript, required_event_ids)
    findings = list(deterministic["findings"])
    if deterministic["result"] == "FIX":
        return report("EDITORIAL_INDEPENDENT_QA", "FIX", findings, manuscript.get("book_id"))
    reviewer = reviewer or {}
    if not reviewer:
        findings.append({"code": "INDEPENDENT_SEMANTIC_REVIEW_REQUIRED"})
        return report("EDITORIAL_INDEPENDENT_QA", "ESCALATE", findings, manuscript.get("book_id"))
    if reviewer.get("id") == manuscript.get("creator", {}).get("id") or not reviewer.get("independent"):
        findings.append({"code": "REVIEWER_NOT_INDEPENDENT", "reviewer_id": reviewer.get("id")})
        return report("EDITORIAL_INDEPENDENT_QA", "ESCALATE", findings, manuscript.get("book_id"))
    missing = sorted(REQUIRED_SEMANTIC_DIMENSIONS - set(reviewer.get("reviewed_dimensions", [])))
    if missing:
        findings.append({"code": "SEMANTIC_DIMENSIONS_NOT_REVIEWED", "dimensions": missing})
        return report("EDITORIAL_INDEPENDENT_QA", "ESCALATE", findings, manuscript.get("book_id"))
    result = reviewer.get("result")
    if result not in {"PASS", "FIX", "ESCALATE"}:
        findings.append({"code": "INVALID_REVIEW_RESULT"})
        result = "ESCALATE"
    findings.extend(reviewer.get("findings", []))
    return report("EDITORIAL_INDEPENDENT_QA", result, findings, manuscript.get("book_id"))
