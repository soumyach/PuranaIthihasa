"""Source-readiness dossiers and source-grounded story packets."""

from pathlib import Path

from .errors import ContractError
from .rules import rules_status
from .util import atomic_json_write, content_hash, load_json, stable_id


READINESS = {"READY", "NEEDS_SOURCE_REVIEW", "INCOMPLETE_SOURCE", "BLOCKED"}
RIGHTS_ALLOWED = {"PERMITTED", "LICENSED", "PUBLIC_DOMAIN_VERIFIED", "OWNED"}
EXAMINATION_ALLOWED = {"READ", "FULLY_READ", "BOUNDED_PASSAGES_EXAMINED", "DECLARED_SCOPE_EXAMINED"}


def _critical(flags):
    return [
        item for item in flags
        if item.get("severity") in {"CRITICAL", "HIGH"}
        or item.get("status") in {"NEEDS_REVIEW", "UNRESOLVED", "BLOCKED"}
    ]


class StoryPacketBuilder:
    """Transform a raw graph packet without filling source gaps."""

    @staticmethod
    def build(raw, book_id=None):
        spine = raw["spine"]
        ordered_events = sorted(raw.get("events", []), key=lambda item: (item.get("sequence", 0), item.get("id", "")))
        claims = []
        for event in ordered_events:
            evidence_ids = sorted(event.get("evidence_ids", []))
            for field in ("cause", "details", "outcome", "consequences"):
                value = event.get(field)
                if value in (None, "", []):
                    continue
                claims.append({
                    "id": stable_id("packet-claim", event["id"], field),
                    "event_id": event["id"],
                    "field": field,
                    "value": value,
                    "classification": "SOURCE_FACT" if evidence_ids else "UNSUPPORTED_SOURCE_GAP",
                    "evidence_ids": evidence_ids,
                })
        entities = []
        for item in raw.get("entities", []):
            entities.append({
                "id": item["id"],
                "name": item.get("name", "UNSPECIFIED"),
                "type": item.get("type", "UNSPECIFIED"),
                "source_scope": item.get("source_scope", spine.get("source_id")),
                "motivation": "UNSPECIFIED",
                "evidence_ids": sorted(item.get("evidence_ids", [])),
            })
        packet = {
            "schema_version": "1.0",
            "spine_id": spine["id"],
            "source_id": spine["source_id"],
            "witness_id": spine.get("witness_id"),
            "source": raw.get("source"),
            "witness": raw.get("witness"),
            "rights_evidence": {
                "witness_status": (raw.get("witness") or {}).get("rights_status", "UNSPECIFIED"),
                "reuse_boundary": "Use graph paraphrases and locators only; do not reproduce third-party website presentation.",
                "project_clearance": "NOT_GRANTED_BY_SOURCE_GRAPH",
            },
            "source_coverage": raw.get("source_coverage", []),
            "independent_full_arc_review": raw.get("independent_full_arc_review", {
                "independent_full_arc_completeness": "UNDETERMINED"
            }),
            "selected_event_ids": raw.get("selected_event_ids", [event["id"] for event in ordered_events]),
            "tradition": (
                (raw.get("source") or {}).get("tradition")
                or (raw.get("source") or {}).get("traditions")
                or "UNSPECIFIED"
            ),
            "frame": spine.get("scope"),
            "bounded_completeness": raw["completeness"],
            "events": ordered_events,
            "characters": entities,
            "relationships": raw.get("relationships", []),
            "conflicts_and_reversals": [
                {
                    "event_id": event["id"],
                    "cause": event.get("cause"),
                    "outcome": event.get("outcome"),
                    "consequences": event.get("consequences", []),
                    "changed_relationship_ids": event.get("changed_relationship_ids", []),
                    "evidence_ids": event.get("evidence_ids", []),
                }
                for event in ordered_events
                if event.get("cause") or event.get("consequences") or event.get("changed_relationship_ids")
            ],
            "manifestations_boons_powers": raw.get("boons_and_powers", []),
            "motivations": [
                {
                    "record_id": item["id"],
                    "motive": item.get("motive", "UNSPECIFIED") or "UNSPECIFIED",
                    "circumstances": item.get("austerity_or_circumstances", "UNSPECIFIED") or "UNSPECIFIED",
                    "evidence_ids": item.get("evidence_ids", []),
                }
                for item in raw.get("boons_and_powers", [])
            ],
            "citations": raw.get("evidence", []),
            "passages": raw.get("passages", []),
            "claims": claims,
            "variants_and_conflicts": raw.get("variants_and_conflicts", []),
            "unresolved_review_flags": raw.get("unresolved_review_flags", []),
            "adaptation_boundaries": [
                {
                    "code": "NO_UNSOURCED_FACTS",
                    "rule": "Every critical factual claim must cite evidence or be explicitly classified as adaptation.",
                },
                {
                    "code": "UNSPECIFIED_STAYS_UNSPECIFIED",
                    "rule": "Missing motivation, iconography, dialogue, chronology, or causality must not be invented.",
                },
                {
                    "code": "BOUNDED_NOT_EXHAUSTIVE",
                    "rule": "A COMPLETE spine covers only its declared bounded chronology.",
                },
            ],
            "graph_hash": raw["graph_hash"],
        }
        if book_id:
            packet["book_id"] = book_id
        packet["packet_hash"] = content_hash(packet)
        packet["id"] = stable_id("story-packet", packet["spine_id"], packet["packet_hash"])
        return packet


class SourceReadinessAssessor:
    def __init__(self, graph, repository_root, packet_loader=None):
        self.graph = graph
        self.root = Path(repository_root)
        self.packet_loader = packet_loader or graph.story_packet

    def assess(self, manifest, mappings=None):
        book_id = manifest.get("id")
        if not book_id:
            raise ContractError("source readiness requires a book id")
        standard = rules_status(self.root)
        blockers = []
        warnings = []
        mapping = mappings or manifest.get("source_mapping") or {
            "outcome": "LEGACY_SPINE_LIST",
            "segments": [{"story_spine_id": item, "event_ids": []} for item in manifest.get("story_spine_ids", [])],
        }
        segments = mapping.get("segments", [])
        spine_ids = [item["story_spine_id"] for item in segments]
        rights_status = manifest.get("rights_status", "UNKNOWN")
        if standard["status"] != "AVAILABLE":
            blockers.append({"code": "RULES_UNAVAILABLE", "status": standard["status"]})
        if rights_status not in RIGHTS_ALLOWED:
            blockers.append({"code": "RIGHTS_NOT_CLEARED", "rights_status": rights_status})
        if not spine_ids:
            blockers.append({"code": "NO_LINKED_STORY_SPINE"})
        packets = []
        for segment in segments:
            spine_id = segment["story_spine_id"]
            try:
                event_ids = segment.get("event_ids") or None
                try:
                    packet = self.packet_loader(spine_id, event_ids)
                except TypeError:
                    packet = self.packet_loader(spine_id)
            except ContractError as exc:
                blockers.append({"code": "UNKNOWN_STORY_SPINE", "spine_id": spine_id, "message": str(exc)})
                continue
            packets.append(packet)
            completeness = packet.get("completeness", {})
            if completeness.get("bounded_spine_status") != "COMPLETE":
                warnings.append({"code": "BOUNDED_ARC_INCOMPLETE", "spine_id": spine_id})
            if completeness.get("chapter_extraction_status") != "COMPLETE":
                warnings.append({
                    "code": "CHAPTER_EXTRACTION_INCOMPLETE",
                    "spine_id": spine_id,
                    "status": completeness.get("chapter_extraction_status", "INCOMPLETE"),
                })
            critical = _critical(packet.get("unresolved_review_flags", []))
            if critical:
                warnings.append({"code": "CRITICAL_REVIEW_FLAGS", "spine_id": spine_id, "flag_ids": [item.get("id") for item in critical]})
            arc_review = packet.get("independent_full_arc_review", {})
            if arc_review.get("independent_full_arc_completeness") != "APPROVED":
                warnings.append({
                    "code": "INDEPENDENT_FULL_ARC_REVIEW_UNDETERMINED",
                    "spine_id": spine_id,
                    "status": arc_review.get("independent_full_arc_completeness", "UNDETERMINED"),
                    "reason": arc_review.get("reason", "No blanket independent approval is recorded."),
                })
            unsupported = [
                claim["id"] for claim in StoryPacketBuilder.build(packet, book_id=book_id)["claims"]
                if claim["classification"] == "UNSUPPORTED_SOURCE_GAP"
            ]
            if unsupported:
                warnings.append({"code": "UNSUPPORTED_CRITICAL_CLAIMS", "spine_id": spine_id, "claim_ids": unsupported})

        graph_examinations = sorted({
            (packet.get("source") or {}).get("examination_status", "UNSPECIFIED")
            for packet in packets
        })
        declared_examination = manifest.get("source_examination_status")
        graph_unspecified = not graph_examinations or set(graph_examinations) == {"UNSPECIFIED"}
        effective_examinations = [declared_examination] if graph_unspecified and declared_examination in EXAMINATION_ALLOWED else graph_examinations
        if not effective_examinations or any(status not in EXAMINATION_ALLOWED for status in effective_examinations):
            warnings.append({
                "code": "SOURCE_EXAMINATION_INCOMPLETE",
                "declared_status": declared_examination or "UNSPECIFIED",
                "graph_statuses": graph_examinations,
            })

        if blockers:
            status = "BLOCKED"
        elif any(item["code"] in {"BOUNDED_ARC_INCOMPLETE", "CHAPTER_EXTRACTION_INCOMPLETE", "SOURCE_EXAMINATION_INCOMPLETE"} for item in warnings):
            status = "INCOMPLETE_SOURCE"
        elif warnings:
            status = "NEEDS_SOURCE_REVIEW"
        else:
            status = "READY"
        dossier = {
            "schema_version": "1.0",
            "book_id": book_id,
            "status": status,
            "graph_hash": self.graph.graph_hash(),
            "rules_hash": standard.get("sha256", "0" * 64),
            "story_spine_ids": list(spine_ids),
            "rights": {"status": rights_status, "notes": manifest.get("rights_notes", [])},
            "dimensions": {
                "bounded_arc": "INCOMPLETE" if any(item["code"] == "BOUNDED_ARC_INCOMPLETE" for item in warnings) else ("COMPLETE" if packets else "UNAVAILABLE"),
                "chapter_extraction": (
                    "NARRATIVE_COMPLETE_ATOMIC_PARTIAL"
                    if packets and all(packet.get("completeness", {}).get("chapter_extraction_status") == "NARRATIVE_COMPLETE_ATOMIC_PARTIAL" for packet in packets)
                    else "INCOMPLETE" if any(item["code"] == "CHAPTER_EXTRACTION_INCOMPLETE" for item in warnings)
                    else "COMPLETE" if packets else "UNAVAILABLE"
                ),
                "source_examination": effective_examinations if effective_examinations else "UNSPECIFIED",
                "critical_flags": "UNRESOLVED" if any(item["code"] in {"CRITICAL_REVIEW_FLAGS", "UNSUPPORTED_CRITICAL_CLAIMS"} for item in warnings) else "CLEAR",
                "independent_full_arc_review": "UNDETERMINED" if any(item["code"] == "INDEPENDENT_FULL_ARC_REVIEW_UNDETERMINED" for item in warnings) else "APPROVED",
                "rights": "CLEARED" if rights_status in RIGHTS_ALLOWED else "BLOCKED",
            },
            "claim_mappings": [
                claim for packet in packets for claim in StoryPacketBuilder.build(packet, book_id=book_id)["claims"]
            ],
            "story_packets": [StoryPacketBuilder.build(packet, book_id=book_id) for packet in packets],
            "blockers": blockers,
            "unresolved_flags": warnings,
            "mapping_outcome": mapping.get("outcome", "UNMAPPED"),
            "controlled_pilot_eligibility": (
                "CONDITIONAL_RIGHTS_AND_INDEPENDENT_REVIEW"
                if mapping.get("outcome") == "VERIFIED_EXACT"
                and packets
                and all(packet.get("completeness", {}).get("bounded_spine_status") == "COMPLETE" for packet in packets)
                and effective_examinations
                and all(status in EXAMINATION_ALLOWED for status in effective_examinations)
                else "NOT_ELIGIBLE"
            ),
            "publication_readiness": "NOT_CERTIFIED",
            "not_exhaustive_scripture_verification": True,
        }
        dossier["dossier_hash"] = content_hash(dossier)
        dossier["id"] = stable_id("source-readiness", book_id, dossier["dossier_hash"])
        return dossier


class DossierStore:
    """Write immutable dossier versions without a mutable pointer."""

    def __init__(self, books_root):
        self.books_root = Path(books_root)

    def put(self, dossier):
        unsigned = {key: value for key, value in dossier.items() if key not in {"dossier_hash", "id", "stored_at"}}
        digest = content_hash(unsigned)
        if dossier.get("dossier_hash") != digest:
            raise ContractError("dossier hash does not match content")
        path = self.books_root / dossier["book_id"] / "source-readiness" / (digest + ".json")
        if path.exists() and load_json(path) != dossier:
            raise ContractError("dossier hash collision")
        if not path.exists():
            atomic_json_write(path, dossier)
        return path


class StoryPacketStore:
    """Persist one immutable copy of a packet for a book."""

    def __init__(self, books_root):
        self.books_root = Path(books_root)

    def put(self, book_id, packet):
        unsigned = {key: value for key, value in packet.items() if key not in {"packet_hash", "id", "stored_at"}}
        digest = content_hash(unsigned)
        if packet.get("packet_hash") != digest:
            raise ContractError("story packet hash does not match content")
        path = self.books_root / book_id / "story-packets" / (digest + ".json")
        if path.exists() and load_json(path) != packet:
            raise ContractError("story packet hash collision")
        if not path.exists():
            atomic_json_write(path, packet)
        return path
