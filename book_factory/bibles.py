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
    manifestations = {}
    entry_ids = set()
    for entry in bible.get("entries", []):
        findings.extend(_required(entry, (
            "id", "name", "identity", "source_scope", "manifestation_rules",
            "required_attributes", "prohibited_attributes", "visual_constants",
            "unspecified_fields", "evidence_ids", "authoritative_source_record",
            "proposed_visual_interpretation", "authorized_weapon_ids", "arm_count_policy",
            "clothing_policy", "ornament_policy", "silhouette_policy", "continuity_checks",
            "allowed_artistic_choices", "forbidden_iconographic_assumptions",
        ), "CHARACTER"))
        if entry.get("id") in entry_ids:
            findings.append({"code": "DUPLICATE_CHARACTER_ID", "entry_id": entry.get("id")})
        entry_ids.add(entry.get("id"))
        if not entry.get("evidence_ids") and not entry.get("unspecified_fields"):
            findings.append({"code": "CHARACTER_EVIDENCE_OR_UNSPECIFIED_REQUIRED", "entry_id": entry.get("id")})
        identity_id = entry.get("identity", {}).get("id") if isinstance(entry.get("identity"), dict) else entry.get("identity")
        if isinstance(entry.get("identity"), dict) and not entry["identity"].get("aliases"):
            findings.append({"code": "CHARACTER_ALIASES_REQUIRED", "entry_id": entry.get("id")})
        identity_signature = (entry.get("name"), entry.get("identity"), entry.get("visual_constants"))
        if identity_id in identities and identities[identity_id] != identity_signature:
            findings.append({"code": "CHARACTER_IDENTITY_CONFLICT", "identity_id": identity_id, "entry_id": entry.get("id")})
        elif identity_id:
            identities[identity_id] = identity_signature
        for manifestation in entry.get("manifestation_rules", []):
            if not manifestation.get("manifestation_id"):
                findings.append({"code": "MANIFESTATION_ID_MISSING", "entry_id": entry.get("id")})
            elif manifestation["manifestation_id"] in manifestations:
                prior_owner = manifestations[manifestation["manifestation_id"]]
                findings.append({
                    "code": (
                        "MANIFESTATION_ID_MERGED_ACROSS_CHARACTERS"
                        if prior_owner != entry.get("id")
                        else "DUPLICATE_MANIFESTATION_ID"
                    ),
                    "manifestation_id": manifestation["manifestation_id"],
                    "entry_ids": [prior_owner, entry.get("id")],
                })
            else:
                manifestations[manifestation["manifestation_id"]] = entry.get("id")
            if manifestation.get("source_scope") != entry.get("source_scope"):
                findings.append({
                    "code": "MANIFESTATION_OUTSIDE_SOURCE_SCOPE",
                    "entry_id": entry.get("id"),
                    "manifestation_id": manifestation.get("manifestation_id"),
                })
        if not isinstance(entry.get("authoritative_source_record"), dict):
            findings.append({"code": "AUTHORITATIVE_SOURCE_RECORD_REQUIRED", "entry_id": entry.get("id")})
        if not isinstance(entry.get("proposed_visual_interpretation"), dict):
            findings.append({"code": "VISUAL_PROPOSAL_RECORD_REQUIRED", "entry_id": entry.get("id")})
        overlap = set(entry.get("authoritative_source_record", {})) & set(entry.get("proposed_visual_interpretation", {}))
        if overlap:
            findings.append({"code": "SOURCE_AND_VISUAL_PROPOSAL_KEYS_OVERLAP", "entry_id": entry.get("id"), "keys": sorted(overlap)})
    return report("CHARACTER_BIBLE", "FIX" if findings else "PASS", findings, subject_id or bible.get("book_id"))


def validate_location_bible(bible, subject_id=None):
    findings = []
    entry_ids = set()
    for entry in bible.get("entries", []):
        findings.extend(_required(entry, (
            "id", "name", "source_scope", "required_features", "prohibited_features",
            "continuity_constants", "unspecified_fields", "evidence_ids",
            "authoritative_source_record", "proposed_visual_interpretation",
            "palette", "lighting", "spatial_anchors", "continuity_checks",
            "architecture_and_landscape", "recurring_scene_elements", "visual_transitions",
            "source_backed_vs_proposed",
        ), "LOCATION"))
        if entry.get("id") in entry_ids:
            findings.append({"code": "DUPLICATE_LOCATION_ID", "entry_id": entry.get("id")})
        entry_ids.add(entry.get("id"))
        if not entry.get("evidence_ids") and not entry.get("unspecified_fields"):
            findings.append({"code": "LOCATION_EVIDENCE_OR_UNSPECIFIED_REQUIRED", "entry_id": entry.get("id")})
        if not isinstance(entry.get("authoritative_source_record"), dict):
            findings.append({"code": "AUTHORITATIVE_SOURCE_RECORD_REQUIRED", "entry_id": entry.get("id")})
        if not isinstance(entry.get("proposed_visual_interpretation"), dict):
            findings.append({"code": "VISUAL_PROPOSAL_RECORD_REQUIRED", "entry_id": entry.get("id")})
        overlap = set(entry.get("authoritative_source_record", {})) & set(entry.get("proposed_visual_interpretation", {}))
        if overlap:
            findings.append({"code": "SOURCE_AND_VISUAL_PROPOSAL_KEYS_OVERLAP", "entry_id": entry.get("id"), "keys": sorted(overlap)})
    return report("LOCATION_BIBLE", "FIX" if findings else "PASS", findings, subject_id or bible.get("book_id"))
