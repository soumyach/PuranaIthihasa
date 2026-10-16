"""Evidence-backed catalogue reconciliation and controlled-pilot ranking."""

from collections import Counter

from .errors import ContractError


class PilotSelector:
    def __init__(self, graph, mapping_registry):
        self.graph = graph
        self.mappings = mapping_registry

    def validate_mappings(self, manifests):
        outcomes = Counter()
        mapped = 0
        for manifest in manifests:
            mapping = self.mappings.resolve(manifest["id"])
            outcomes[mapping["outcome"]] += 1
            for segment in mapping.get("segments", []):
                spine = self.graph.story_spine(segment["story_spine_id"])
                event_ids = segment.get("event_ids", [])
                if event_ids and not set(event_ids).issubset(set(spine["event_ids"])):
                    raise ContractError("catalogue mapping includes events outside its spine", {"book_id": manifest["id"]})
                mapped += 1
        return {"outcomes": dict(sorted(outcomes.items())), "validated_segments": mapped}

    def rank(self, manifests, dossiers):
        manifest_index = {item["id"]: item for item in manifests}
        dossier_index = {item["book_id"]: item for item in dossiers}
        ranked = []
        for configured in sorted(self.mappings.pilot_ranking(), key=lambda item: item["rank"]):
            book = manifest_index[configured["book_id"]]
            if book.get("edition_status") == "EXISTING_EDITION" or not book.get("automatic_production_eligible", True):
                continue
            dossier = dossier_index[book["id"]]
            packet_counts = {
                "events": sum(len(item.get("events", [])) for item in dossier["story_packets"]),
                "citations": sum(len(item.get("citations", [])) for item in dossier["story_packets"]),
                "characters": sum(len(item.get("characters", [])) for item in dossier["story_packets"]),
                "powers": sum(len(item.get("manifestations_boons_powers", [])) for item in dossier["story_packets"]),
            }
            ranked.append({
                **configured,
                "title": book["title"],
                "mapping_outcome": dossier["mapping_outcome"],
                "source_readiness": dossier["status"],
                "controlled_pilot_eligibility": dossier["controlled_pilot_eligibility"],
                "publication_readiness": dossier["publication_readiness"],
                "evidence": packet_counts,
                "blockers": dossier["blockers"],
                "source_limitations": dossier["unresolved_flags"],
            })
        return ranked


def catalogue_readiness_report(catalogue, mapping_validation, dossiers, ranked):
    declared = Counter(item["graph_readiness"] for item in catalogue["books"])
    factory = Counter(item["readiness"] for item in catalogue["books"])
    strict_ready = [item["book_id"] for item in dossiers if item["status"] == "READY"]
    return {
        "schema_version": "1.0",
        "catalogue_sha256": catalogue["metadata"]["source_sha256"],
        "books": len(catalogue["books"]),
        "collections": len(catalogue["collections"]),
        "declared_roadmap_counts": dict(sorted(declared.items())),
        "factory_readiness_counts": dict(sorted(factory.items())),
        "mapping_validation": mapping_validation,
        "strictly_ready_book_ids": strict_ready,
        "strictly_ready_count": len(strict_ready),
        "controlled_pilot_policy": {
            "meaning": "A complete bounded event arc may enter source-controlled pre-production while chapter atomization, rights clearance, and independent review remain visible blockers.",
            "does_not_mean": "publication ready, source certified, rights cleared, or editorially approved",
        },
        "top_conditional_finalists": ranked,
        "selected_pilot": "DM04",
        "selected_pilot_basis": "Best combination of exact graph mapping, self-contained full arc, visual range, and enough scope to exercise the complete future pipeline.",
        "dm08_excluded": True,
    }
