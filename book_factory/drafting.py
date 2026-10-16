"""Provider-bound manuscript requests; this module never drafts prose itself."""

from .util import content_hash, stable_id


def build_manuscript_request(manifest, dossier, packets, rules_hash):
    required_events = [event["id"] for packet in packets for event in packet.get("events", [])]
    request = {
        "schema_version": "1.0",
        "book_id": manifest["id"],
        "title": manifest["title"],
        "scope": manifest.get("scope"),
        "audience": "family readers; exact age band requires editorial confirmation",
        "dossier_hash": dossier["dossier_hash"],
        "packet_hashes": [packet["packet_hash"] for packet in packets],
        "graph_hash": dossier["graph_hash"],
        "rules_hash": rules_hash,
        "required_event_ids": required_events,
        "evidence": [citation for packet in packets for citation in packet.get("citations", [])],
        "characters": [character for packet in packets for character in packet.get("characters", [])],
        "relationships": [relationship for packet in packets for relationship in packet.get("relationships", [])],
        "manifestations_boons_powers": [item for packet in packets for item in packet.get("manifestations_boons_powers", [])],
        "continuity_references": {
            "character_bible_hash": None,
            "location_bible_hash": None,
            "status": "NOT_PREPARED_IN_THIS_MILESTONE",
        },
        "source_classification_rules": [
            "Source claims must be MULA or SAMPRADAYA and cite evidence.",
            "Narrative bridges must be DRISHTI and visibly labelled in the claim map.",
            "Invented material must be KALPANA and may not change doctrine, identity, causality, or outcome.",
        ],
        "literary_benchmark": {
            "path": "book-factory/references/literary-benchmarks/The_Enemy_Who_Multiplied_Manuscript_v2.md",
            "sha256": "6684d61e7c8f58a3fc3d851d7e8cbc7d13eb1e42105dbb9d011c1e7453791865",
            "use": "quality benchmark only; do not copy or reproduce",
        },
        "required_sections": ["opening", "context", "beats", "climax", "aftermath", "ending", "claim_map", "dialogue"],
        "literary_completeness": [
            "Build a complete narrative arc rather than caption expansion.",
            "Include cause, escalation, reversals, climax, aftermath, and a resolved ending.",
            "Keep narration and dialogue structured and non-duplicative.",
            "Place any next-book hook only after the present story has fully ended.",
        ],
    }
    request["request_hash"] = content_hash(request)
    request["operation_key"] = stable_id("draft-manuscript", manifest["id"], request["request_hash"])
    return request


def targeted_revision_request(review_record):
    findings = [item for item in review_record.get("findings", []) if item.get("code")]
    request = {
        "schema_version": "1.0",
        "book_id": review_record["book_id"],
        "review_hash": review_record["review_hash"],
        "finding_ids": [item["code"] for item in findings],
        "affected_sections": sorted({section for item in findings for section in item.get("section_ids", [])}),
        "bounded_excerpts": [item["excerpt"] for item in findings if item.get("excerpt")],
        "constraint": "Repair only listed findings and affected sections; preserve all approved source choices and unrelated text.",
    }
    request["request_hash"] = content_hash(request)
    return request
