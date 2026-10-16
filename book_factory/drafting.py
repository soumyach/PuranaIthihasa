"""Evidence-bound manuscript and review requests; this module drafts no prose."""

from .editorial import PR5_REVIEW_PERSPECTIVES, REQUIRED_SEMANTIC_DIMENSIONS
from .util import content_hash, stable_id


def build_manuscript_request(manifest, dossier, packets, rules_hash, clearance=None,
                             parent_manuscript=None, revision_request=None,
                             milestone_contract=None):
    required_events = [event["id"] for packet in packets for event in packet.get("events", [])]
    allowed_evidence_ids = sorted({
        citation["id"] for packet in packets for citation in packet.get("citations", [])
    })
    request = {
        "schema_version": "1.0",
        "book_id": manifest["id"],
        "title": manifest["title"],
        "scope": manifest.get("scope"),
        "audience": (
            "family read-aloud and independent readers approximately age 10+"
            if milestone_contract else
            "family readers; exact age band requires editorial confirmation"
        ),
        "dossier_hash": dossier["dossier_hash"],
        "packet_hashes": [packet["packet_hash"] for packet in packets],
        "graph_hash": dossier["graph_hash"],
        "rules_hash": rules_hash,
        "source_clearance_hash": (clearance or {}).get("clearance_hash"),
        "private_draft_gate": (clearance or {}).get("private_draft_gate", "NOT_CLEARED"),
        "publication_gate": (clearance or {}).get("publication_gate", "BLOCKED"),
        "required_event_ids": required_events,
        "event_requirements": [
            {
                "event_id": event["id"],
                "sequence": event.get("sequence"),
                "summary": event.get("summary"),
                "cause": event.get("cause"),
                "details": event.get("details"),
                "outcome": event.get("outcome"),
                "consequences": event.get("consequences", []),
                "evidence_ids": sorted(event.get("evidence_ids", [])),
            }
            for packet in packets for event in packet.get("events", [])
        ],
        "allowed_evidence_ids": allowed_evidence_ids,
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
        "rights_constraints": [
            "Write fresh original English prose from evidence paraphrases and locators.",
            "Do not reproduce Wisdomlib presentation, OCR, synopsis, or another modern translation.",
            "Do not reproduce the SanskritDocuments transcription.",
            "Do not present created dialogue as a direct scripture quotation.",
            "This is a private editorial draft; publication remains blocked.",
        ],
        "family_reading_constraints": [
            "Use accessible English without academic diacritics in the literary text.",
            "Make battle consequences clear without lingering graphic detail.",
            "Avoid contextless catalogues of divine names and weapons.",
            "Give the story quiet moments, reversals, emotional progression, and a resolved ending.",
        ],
        "parent_manuscript_hash": (parent_manuscript or {}).get("content_hash"),
        "revision_request": revision_request,
        "milestone_contract": milestone_contract,
    }
    request["request_hash"] = content_hash(request)
    request["operation_key"] = stable_id("draft-manuscript", manifest["id"], request["request_hash"])
    return request


def build_review_request(manuscript_record, packet_hashes, required_event_ids,
                         dossier_hash, clearance_hash, packets=None,
                         perspective="LEGACY_COMBINED"):
    manuscript = manuscript_record["payload"]
    dimensions = (
        sorted(PR5_REVIEW_PERSPECTIVES[perspective])
        if perspective in PR5_REVIEW_PERSPECTIVES else
        sorted(REQUIRED_SEMANTIC_DIMENSIONS)
    )
    request = {
        "schema_version": "1.0",
        "book_id": manuscript_record["book_id"],
        "reviewed_manuscript_hash": manuscript_record["content_hash"],
        "reviewed_packet_hashes": sorted(packet_hashes),
        "dossier_hash": dossier_hash,
        "source_clearance_hash": clearance_hash,
        "writer_id": manuscript.get("creator", {}).get("id"),
        "required_event_ids": list(required_event_ids),
        "review_perspective": perspective,
        "required_dimensions": dimensions,
        "require_source_event_checks": perspective != "LITERARY_EXPERIENCE",
        "manuscript": manuscript,
        "locked_source_evidence": [
            {
                "packet_hash": packet["packet_hash"],
                "events": packet.get("events", []),
                "citations": packet.get("citations", []),
                "variants_and_conflicts": packet.get("variants_and_conflicts", []),
                "adaptation_boundaries": packet.get("adaptation_boundaries", []),
            }
            for packet in (packets or [])
        ],
        "constraints": [
            "Review the immutable version; do not rewrite it in place.",
            "Tie source-fidelity findings to event, claim, and evidence ids.",
            "Return PASS, FIX, or ESCALATE; critical findings cannot average to PASS.",
            "Do not certify publication readiness, legal clearance, or theological authority.",
        ],
    }
    request["request_hash"] = content_hash(request)
    request["operation_key"] = stable_id("review-manuscript", manuscript_record["book_id"], request["request_hash"])
    return request


def pr5_quality_revision_request(manuscript_record, prior_review_record):
    """Authorize the explicit PR5 literary pass without mislabelling it a FIX."""
    request = {
        "schema_version": "1.0",
        "book_id": manuscript_record["book_id"],
        "milestone": "PR5_VISUAL_PREPRODUCTION",
        "revision_kind": "AUTHORIZED_LITERARY_QUALITY_REVISION",
        "parent_manuscript_hash": manuscript_record["content_hash"],
        "prior_pass_review_hash": prior_review_record["payload"]["review_hash"],
        "preserve_required_event_ids": ["dm-event-%03d" % number for number in range(8, 24)],
        "audience": "family read-aloud and independent readers approximately age 10+",
        "required_improvements": [
            "Open with a stronger forest-frame scene and a compelling question.",
            "Give Suratha and Samadhi meaningful listener reactions, labelled as literary adaptation.",
            "Use natural dialogue and reactions without presenting invented words as scripture.",
            "Reduce commander-name exposition while retaining every sourced event.",
            "Give Devi's manifestation more dramatic space and make the arming sequence memorable.",
            "Make Mahishasura's arrival a reversal and separate his transformations into escalating beats.",
            "Remove the duplicated transformation summary in chapter 6 and reduce battle recap in chapter 7.",
            "Preserve the attributed hymn, boon request, grant and disappearance.",
            "Close with an accessible reflection and a natural transition to the next volume only after resolution.",
        ],
        "source_constraints": [
            "Preserve the sixteen locked source events, their sequence and theological distinctions.",
            "Do not introduce canonical claims outside the locked packet.",
            "Label new framing dialogue and listener business DRISHTI or KALPANA in the claim map.",
            "Keep the hymn's theology attributed to the gods and do not certify theological authority.",
        ],
        "benchmark": "Use DM08/Raktabija Manuscript v2 only as a literary-quality benchmark; do not copy it.",
    }
    request["request_hash"] = content_hash(request)
    return request


def targeted_revision_request(review_record):
    findings = [item for item in review_record.get("findings", []) if item.get("code")]
    bounded_excerpts = []
    for item in findings:
        if item.get("excerpt"):
            bounded_excerpts.append(item["excerpt"])
        bounded_excerpts.extend(item.get("additional_bounded_excerpts", []))
    request = {
        "schema_version": "1.0",
        "book_id": review_record["book_id"],
        "review_hash": review_record["review_hash"],
        "reviewed_manuscript_hash": review_record.get("reviewed_manuscript_hash"),
        "finding_ids": [item["code"] for item in findings],
        "affected_sections": sorted({section for item in findings for section in item.get("section_ids", [])}),
        "bounded_excerpts": bounded_excerpts,
        "constraint": "Repair only listed findings and affected sections; preserve all approved source choices and unrelated text.",
    }
    request["request_hash"] = content_hash(request)
    return request


def render_manuscript_markdown(manuscript):
    """Render the structured literary chapters without hiding provenance in prose."""
    lines = ["# %s" % manuscript["title"], "", "*%s*" % manuscript.get("subtitle", "A Khatakshetra retelling"), ""]
    for chapter in manuscript.get("chapters", []):
        lines.extend(["## %s" % chapter["title"], "", chapter["text"].strip(), ""])
    lines.extend([
        "---",
        "",
        "## Editorial source note",
        "",
        manuscript.get("source_note", "This private editorial draft remains blocked from publication."),
        "",
    ])
    return "\n".join(lines)
