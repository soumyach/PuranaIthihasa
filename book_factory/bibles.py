"""Character and location bible contract checks."""

from .quality import report


def _required(entry, fields, kind):
    return [
        {"code": "MISSING_%s_FIELD" % kind, "entry_id": entry.get("id"), "field": field}
        for field in fields if field not in entry
    ]


def validate_character_bible(bible, subject_id=None):
    findings = []
    identities = {}
    for entry in bible.get("entries", []):
        findings.extend(_required(entry, (
            "id", "name", "identity", "source_scope", "manifestation_rules",
            "required_attributes", "prohibited_attributes", "visual_constants",
            "unspecified_fields", "evidence_ids",
        ), "CHARACTER"))
        if not entry.get("evidence_ids") and not entry.get("unspecified_fields"):
            findings.append({"code": "CHARACTER_EVIDENCE_OR_UNSPECIFIED_REQUIRED", "entry_id": entry.get("id")})
        identity_id = entry.get("identity", {}).get("id") if isinstance(entry.get("identity"), dict) else entry.get("identity")
        identity_signature = (entry.get("name"), entry.get("identity"), entry.get("visual_constants"))
        if identity_id in identities and identities[identity_id] != identity_signature:
            findings.append({"code": "CHARACTER_IDENTITY_CONFLICT", "identity_id": identity_id, "entry_id": entry.get("id")})
        elif identity_id:
            identities[identity_id] = identity_signature
        for manifestation in entry.get("manifestation_rules", []):
            if manifestation.get("source_scope") != entry.get("source_scope"):
                findings.append({
                    "code": "MANIFESTATION_OUTSIDE_SOURCE_SCOPE",
                    "entry_id": entry.get("id"),
                    "manifestation_id": manifestation.get("manifestation_id"),
                })
    return report("CHARACTER_BIBLE", "FIX" if findings else "PASS", findings, subject_id or bible.get("book_id"))


def validate_location_bible(bible, subject_id=None):
    findings = []
    for entry in bible.get("entries", []):
        findings.extend(_required(entry, (
            "id", "name", "source_scope", "required_features", "prohibited_features",
            "continuity_constants", "unspecified_fields", "evidence_ids",
        ), "LOCATION"))
        if not entry.get("evidence_ids") and not entry.get("unspecified_fields"):
            findings.append({"code": "LOCATION_EVIDENCE_OR_UNSPECIFIED_REQUIRED", "entry_id": entry.get("id")})
    return report("LOCATION_BIBLE", "FIX" if findings else "PASS", findings, subject_id or bible.get("book_id"))
