import copy
import tempfile
import unittest
from pathlib import Path

from book_factory.approvals import ApprovalStore
from book_factory.bibles import validate_character_bible
from book_factory.catalogue import CatalogueStore
from book_factory.editorial import editorial_review
from book_factory.narrative import validate_manuscript
from book_factory.source_graph import ReadOnlySourceGraph
from book_factory.source_intelligence import (
    DossierStore,
    SourceReadinessAssessor,
    StoryPacketBuilder,
    StoryPacketStore,
)
from book_factory.util import atomic_json_write, load_json, tree_snapshot


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "book-factory" / "fixtures" / "source-intelligence" / "fictional-story-packet.json"


class FictionalGraph:
    def __init__(self, packet):
        self.packet = packet

    def story_packet(self, spine_id):
        if spine_id != self.packet["spine"]["id"]:
            from book_factory.errors import ContractError
            raise ContractError("unknown fictional spine")
        return copy.deepcopy(self.packet)

    def graph_hash(self):
        return self.packet["graph_hash"]


def fictional_manifest(rights="OWNED"):
    return {
        "id": "fictional-paper-moon-book",
        "title": "The Paper Moon Observatory",
        "line": "KATHAS",
        "readiness": "NEEDS_SOURCE_REVIEW",
        "collection_ids": ["fictional-moon-shelf"],
        "story_spine_ids": ["moon-archive-spine"],
        "rights_status": rights,
        "source_examination_status": "BOUNDED_PASSAGES_EXAMINED",
    }


def valid_manuscript():
    return {
        "book_id": "fictional-paper-moon-book",
        "version": 1,
        "title": "The Paper Moon Observatory",
        "audience": "fictional family readers ages 8-12",
        "opening": "Eli unfolds a paper sky-map.",
        "context": "A wholly fictional moon archive.",
        "beats": [
            {"id": "beat-1", "event_ids": ["moon-archive-event-1"]},
            {"id": "beat-2", "event_ids": ["moon-archive-event-2"]},
        ],
        "ending": "Eli records the observatory and safely returns.",
        "ending_before_next_book_hook": True,
        "next_book_hook": "Another folded map waits.",
        "source_classification": "KALPANA",
        "source_packet_hash": "b" * 64,
        "claim_map": [
            {
                "id": "claim-1",
                "beat_id": "beat-1",
                "source_class": "MULA",
                "evidence_ids": ["moon-archive-evidence-1"],
            },
            {
                "id": "claim-2",
                "beat_id": "beat-2",
                "source_class": "KALPANA",
                "evidence_ids": [],
                "adaptation_note": "Fictional bridge declared by the fixture author.",
            },
        ],
        "dialogue": [],
        "creator": {"id": "fictional-writer"},
    }


class FoundationPR2SyntheticTests(unittest.TestCase):
    def setUp(self):
        self.raw = load_json(FIXTURE)
        self.graph = FictionalGraph(self.raw)

    def test_01_correct_story_spine_extraction(self):
        packet = StoryPacketBuilder.build(self.graph.story_packet("moon-archive-spine"))
        self.assertEqual(packet["spine_id"], "moon-archive-spine")
        self.assertEqual(packet["source_id"], "fictional-moon-archive")
        self.assertTrue(packet["bounded_completeness"]["not_exhaustive_scripture_verification"])

    def test_02_correct_ordered_event_retrieval(self):
        packet = StoryPacketBuilder.build(self.raw)
        self.assertEqual([event["sequence"] for event in packet["events"]], [1, 2])

    def test_03_stable_source_evidence_references(self):
        first = StoryPacketBuilder.build(self.raw)
        second = StoryPacketBuilder.build(copy.deepcopy(self.raw))
        self.assertEqual(first["packet_hash"], second["packet_hash"])
        self.assertEqual(first["citations"], second["citations"])

    def test_04_readiness_rejects_incomplete_coverage(self):
        raw = copy.deepcopy(self.raw)
        raw["completeness"]["chapter_extraction_status"] = "INCOMPLETE"
        assessor = SourceReadinessAssessor(FictionalGraph(raw), ROOT)
        self.assertEqual(assessor.assess(fictional_manifest())["status"], "INCOMPLETE_SOURCE")

    def test_05_readiness_rejects_unresolved_critical_contradictions(self):
        raw = copy.deepcopy(self.raw)
        raw["unresolved_review_flags"] = [{"id": "fictional-conflict", "severity": "CRITICAL", "status": "UNRESOLVED"}]
        assessor = SourceReadinessAssessor(FictionalGraph(raw), ROOT)
        self.assertEqual(assessor.assess(fictional_manifest())["status"], "NEEDS_SOURCE_REVIEW")

    def test_06_rights_blocked_candidate_handling(self):
        dossier = SourceReadinessAssessor(self.graph, ROOT).assess(fictional_manifest("UNKNOWN"))
        self.assertEqual(dossier["status"], "BLOCKED")
        self.assertIn("RIGHTS_NOT_CLEARED", {item["code"] for item in dossier["blockers"]})

    def test_07_exact_preservation_of_catalogue_ids(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            current = root / "catalogue.json"
            incoming = root / "incoming.json"
            atomic_json_write(current, {"schema_version": "1.0", "collections": [], "books": []})
            atomic_json_write(incoming, {
                "schema_version": "1.0",
                "collections": [{"id": "fictional-moon-shelf", "title": "Fictional Moon Shelf"}],
                "books": [fictional_manifest()],
            })
            merged = CatalogueStore(current).import_file(incoming)
            self.assertEqual(merged["books"][0]["id"], "fictional-paper-moon-book")
            self.assertEqual(merged["books"][0]["collection_ids"], ["fictional-moon-shelf"])

    def test_08_missing_event_detection(self):
        manuscript = valid_manuscript()
        manuscript["beats"] = manuscript["beats"][:1]
        result = validate_manuscript(manuscript, ["moon-archive-event-1", "moon-archive-event-2"])
        self.assertIn("MISSING_REQUIRED_EVENT", {item["code"] for item in result["findings"]})

    def test_09_unsupported_claim_detection(self):
        manuscript = valid_manuscript()
        manuscript["claim_map"][0]["evidence_ids"] = []
        result = validate_manuscript(manuscript, ["moon-archive-event-1", "moon-archive-event-2"])
        self.assertIn("UNSUPPORTED_SOURCE_CLAIM", {item["code"] for item in result["findings"]})

    def test_10_direct_source_claims_are_distinct_from_adaptation(self):
        result = validate_manuscript(valid_manuscript(), ["moon-archive-event-1", "moon-archive-event-2"])
        self.assertEqual(result["result"], "PASS")

    def test_11_character_identity_consistency(self):
        bible = {
            "book_id": "fictional-paper-moon-book",
            "entries": [
                {"id": "eli-a", "name": "Captain Eli", "identity": {"id": "eli"}, "source_scope": "fictional-moon-archive", "manifestation_rules": [], "required_attributes": [], "prohibited_attributes": [], "visual_constants": {"coat": "blue"}, "unspecified_fields": [], "evidence_ids": ["moon-archive-evidence-1"]},
                {"id": "eli-b", "name": "Captain Eliot", "identity": {"id": "eli"}, "source_scope": "fictional-moon-archive", "manifestation_rules": [], "required_attributes": [], "prohibited_attributes": [], "visual_constants": {"coat": "red"}, "unspecified_fields": [], "evidence_ids": ["moon-archive-evidence-1"]},
            ],
        }
        self.assertIn("CHARACTER_IDENTITY_CONFLICT", {item["code"] for item in validate_character_bible(bible)["findings"]})

    def test_12_source_scoped_manifestations(self):
        bible = {
            "book_id": "fictional-paper-moon-book",
            "entries": [{"id": "moon-guide", "name": "Moon Guide", "identity": {"id": "moon-guide"}, "source_scope": "fictional-moon-archive", "manifestation_rules": [{"manifestation_id": "sun-guide-form", "source_scope": "unrelated-sun-archive"}], "required_attributes": [], "prohibited_attributes": [], "visual_constants": {}, "unspecified_fields": [], "evidence_ids": ["moon-archive-evidence-1"]}],
        }
        self.assertIn("MANIFESTATION_OUTSIDE_SOURCE_SCOPE", {item["code"] for item in validate_character_bible(bible)["findings"]})

    def test_13_approval_inheritance_and_invalidation(self):
        with tempfile.TemporaryDirectory() as temporary:
            store = ApprovalStore(temporary)
            record = store.create(
                "COLLECTION_STYLE", "VISUAL_STYLE", "c" * 64,
                {"type": "collection", "id": "fictional-moon-shelf"},
                {"kind": "human", "id": "fictional-reviewer"},
                {"kind": "worker", "id": "fictional-artist"}, "PASS",
                inheritance_allowed=True, source_scope="fictional-moon-archive",
                tradition_id="fictional-paper-tradition", edition_id="fixture-v1",
                evidence_hash="d" * 64,
            )
            target = {"type": "book", "id": "fictional-paper-moon-book", "ancestors": ["fictional-moon-shelf"]}
            context = {"source_scope": "fictional-moon-archive", "tradition_id": "fictional-paper-tradition", "edition_id": "fixture-v1"}
            self.assertEqual(store.find_valid("VISUAL_STYLE", "c" * 64, target, target_context=context, current_evidence_hash="d" * 64)["id"], record["id"])
            self.assertIsNone(store.find_valid("VISUAL_STYLE", "c" * 64, target, target_context=context, current_evidence_hash="e" * 64))
            wrong = dict(context, tradition_id="unrelated-fictional-tradition")
            self.assertIsNone(store.find_valid("VISUAL_STYLE", "c" * 64, target, target_context=wrong, current_evidence_hash="d" * 64))

    def test_14_editorial_gate_needs_independent_review(self):
        result = editorial_review(valid_manuscript(), ["moon-archive-event-1", "moon-archive-event-2"])
        self.assertEqual(result["result"], "ESCALATE")

    def test_15_resuming_outputs_does_not_duplicate_versions(self):
        packet = StoryPacketBuilder.build(self.raw)
        dossier = SourceReadinessAssessor(self.graph, ROOT).assess(fictional_manifest())
        with tempfile.TemporaryDirectory() as temporary:
            books = Path(temporary)
            self.assertEqual(DossierStore(books).put(dossier), DossierStore(books).put(dossier))
            self.assertEqual(StoryPacketStore(books).put(dossier["book_id"], packet), StoryPacketStore(books).put(dossier["book_id"], packet))
            self.assertEqual(len(list(books.rglob("*.json"))), 2)

    def test_16_source_graph_remains_byte_for_byte_unchanged(self):
        graph_root = ROOT / "research" / "source-graph"
        before = tree_snapshot(graph_root)
        graph = ReadOnlySourceGraph(graph_root)
        graph.verify()
        graph.story_packet(graph.complete_story_spines()[0]["id"])
        self.assertEqual(before, tree_snapshot(graph_root))


if __name__ == "__main__":
    unittest.main()
