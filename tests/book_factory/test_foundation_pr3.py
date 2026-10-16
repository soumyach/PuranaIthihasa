import copy
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from book_factory.artifacts import ArtifactStore
from book_factory.catalogue import CatalogueStore
from book_factory.catalogue_v01 import EXPECTED_CATALOGUE_SHA256, SourceMappingRegistry, import_authoritative_v01
from book_factory.director import FactoryDirector
from book_factory.drafting import targeted_revision_request
from book_factory.editorial import editorial_review
from book_factory.errors import ContractError
from book_factory.pilot import PilotSelector
from book_factory.references import ReferenceEditionRegistry
from book_factory.source_graph import ReadOnlySourceGraph
from book_factory.source_intelligence import DossierStore, StoryPacketStore
from book_factory.state import StateStore
from book_factory.util import load_json, sha256_bytes, tree_snapshot
from book_factory.versioning import EditorialReviewStore, ManuscriptVersionStore


ROOT = Path(__file__).resolve().parents[2]
RAW_CATALOGUE = ROOT / "book-factory" / "inputs" / "catalogues" / "Khatakshetra_Illustrated_Library_Catalogue_v0.1.json"
MAPPINGS = ROOT / "book-factory" / "config" / "catalogue-source-mappings.json"


def minimal_manuscript():
    return {
        "book_id": "fictional-book",
        "version": 1,
        "title": "Fictional",
        "audience": "8-12",
        "opening": "Open",
        "context": "Context",
        "beats": [{"id": "beat-1", "event_ids": ["event-1"]}],
        "ending": "End",
        "source_classification": "KALPANA",
        "claim_map": [{"id": "claim-1", "beat_id": "beat-1", "source_class": "KALPANA", "adaptation_note": "fixture"}],
        "dialogue": [],
        "creator": {"id": "writer"},
    }


class FoundationPR3Tests(unittest.TestCase):
    def test_authoritative_catalogue_hash_shape_and_lossless_fields(self):
        self.assertEqual(sha256_bytes(RAW_CATALOGUE.read_bytes()), EXPECTED_CATALOGUE_SHA256)
        raw = load_json(RAW_CATALOGUE)
        normalized = import_authoritative_v01(RAW_CATALOGUE, SourceMappingRegistry(MAPPINGS))
        self.assertEqual(normalized, load_json(ROOT / "books" / "catalogue.json"))
        self.assertEqual((len(normalized["books"]), len(normalized["collections"])), (78, 12))
        self.assertEqual({item["id"] for item in normalized["books"]}, {item["id"] for item in raw["books"]})
        self.assertEqual(normalized["metadata"]["counts"], raw["counts"])
        for item in normalized["books"]:
            self.assertEqual(item["original"], next(raw_item for raw_item in raw["books"] if raw_item["id"] == item["id"]))

    def test_all_mapping_outcomes_are_explicit_and_graph_valid(self):
        catalogue = load_json(ROOT / "books" / "catalogue.json")
        graph = ReadOnlySourceGraph(ROOT / "research" / "source-graph")
        result = PilotSelector(graph, SourceMappingRegistry(MAPPINGS)).validate_mappings(catalogue["books"])
        self.assertEqual(sum(result["outcomes"].values()), 78)
        self.assertEqual(result["outcomes"], {"UNMAPPED": 56, "VERIFIED_EXACT": 4, "VERIFIED_SUBSET": 18})

    def test_dm08_is_reference_only_with_separate_statuses_and_exact_assets(self):
        dm08 = CatalogueStore(ROOT / "books" / "catalogue.json").get("DM08")
        self.assertEqual(dm08["edition_status"], "EXISTING_EDITION")
        self.assertFalse(dm08["automatic_production_eligible"])
        self.assertNotEqual(dm08["publication_readiness_status"], dm08["source_verification_status"])
        edition = load_json(ROOT / "book-factory" / "references" / "editions" / "DM08.json")
        self.assertEqual(edition["scope_reconciliation"]["status"], "MISMATCH_REQUIRES_INDEPENDENT_SOURCE_VERIFICATION")
        manuscript = next(item for item in edition["assets"] if item["kind"] == "MANUSCRIPT_MARKDOWN")
        self.assertEqual(sha256_bytes((ROOT / manuscript["path"]).read_bytes()), manuscript["sha256"])
        with self.assertRaises(ContractError):
            FactoryDirector(ROOT).prepare_pilot("DM08")

    def test_missing_local_pdf_is_reported_but_not_fatal(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "schemas" / "book-factory").mkdir(parents=True)
            shutil.copy(ROOT / "schemas" / "book-factory" / "reference-edition.schema.json", root / "schemas" / "book-factory")
            (root / "book-factory" / "references" / "editions").mkdir(parents=True)
            record = load_json(ROOT / "book-factory" / "references" / "editions" / "DM08.json")
            (root / "book-factory" / "references" / "editions" / "DM08.json").write_text(json.dumps(record), encoding="utf-8")
            manuscript = next(item for item in record["assets"] if item["kind"] == "MANUSCRIPT_MARKDOWN")
            manuscript_path = root / manuscript["path"]
            manuscript_path.parent.mkdir(parents=True)
            shutil.copy(ROOT / manuscript["path"], manuscript_path)
            result = ReferenceEditionRegistry(root).verify("DM08")
            self.assertEqual(result["assets"][0]["availability"], "MISSING_LOCAL_REFERENCE")

    def test_candidate_ranking_is_honest_and_excludes_dm08(self):
        report = FactoryDirector(ROOT).evaluate_catalogue(False)
        self.assertEqual(report["strictly_ready_count"], 0)
        self.assertEqual([item["book_id"] for item in report["top_conditional_finalists"]], ["DM04", "DM02", "DM01"])
        self.assertNotIn("DM08", [item["book_id"] for item in report["top_conditional_finalists"]])
        self.assertEqual(report["selected_pilot"], "DM04")

    def test_pilot_contains_only_dossier_and_scoped_story_packet(self):
        manuscript_count = len(ManuscriptVersionStore(ROOT / "books").versions("DM04"))
        result = FactoryDirector(ROOT).prepare_pilot("DM04")
        self.assertEqual(result["status"], "PREPARED_CONDITIONAL")
        self.assertFalse(result["generated_manuscript"])
        packet = load_json(Path(result["story_packet_paths"][0]))
        self.assertEqual(packet["book_id"], "DM04")
        self.assertEqual(len(packet["selected_event_ids"]), 16)
        self.assertEqual(len(ManuscriptVersionStore(ROOT / "books").versions("DM04")), manuscript_count)

    def test_draft_and_review_fail_honestly_without_provider(self):
        director = FactoryDirector(ROOT)
        drafted = director.draft_manuscript("DM04", True)
        reviewed = director.review_manuscript("DM04")
        self.assertEqual(drafted["status"], "BLOCKED_PROVIDER")
        self.assertFalse(drafted["manuscript_created"])
        self.assertEqual(reviewed["status"], "BLOCKED_REVIEWER")
        self.assertFalse(reviewed["review_created"])

    def test_resume_rechecks_provider_without_duplicate_events(self):
        with tempfile.TemporaryDirectory() as temporary:
            books = Path(temporary) / "books"
            books.mkdir()
            catalogue = {
                "schema_version": "1.0",
                "collections": [],
                "books": [{"id": "fictional-book", "title": "Fictional", "line": "KATHAS", "readiness": "READY", "collection_ids": []}],
            }
            (books / "catalogue.json").write_text(json.dumps(catalogue), encoding="utf-8")
            state = StateStore(books, "fictional-book")
            state.initialize()
            state.transition("SOURCE_CHECK", "source")
            state.transition("MANUSCRIPT", "source-complete")
            state.transition("BLOCKED", "no-provider", recovery={"reason": "provider absent", "resume_stage": "MANUSCRIPT"})
            event_count = len(state._events())
            director = FactoryDirector(ROOT)
            director.books_root = books
            director.catalogue = CatalogueStore(books / "catalogue.json")
            first = director.resume("fictional-book")
            second = director.resume("fictional-book")
            self.assertEqual(first["status"], "BLOCKED_PROVIDER")
            self.assertEqual(first, second)
            self.assertEqual(len(state._events()), event_count)

    def test_unverified_reviewer_dictionary_cannot_pass(self):
        reviewer = {
            "id": "reviewer",
            "independent": True,
            "reviewed_dimensions": ["clarity", "pacing", "age_suitability", "dignity", "identity_distinctness", "source_fidelity"],
            "result": "PASS",
        }
        self.assertEqual(editorial_review(minimal_manuscript(), ["event-1"], reviewer)["result"], "ESCALATE")

    def test_versioning_is_parent_linked_immutable_and_idempotent(self):
        with tempfile.TemporaryDirectory() as temporary:
            manuscripts = ManuscriptVersionStore(temporary)
            first = manuscripts.put("fictional-book", {"text": "v1"})
            self.assertEqual(first, manuscripts.put("fictional-book", {"text": "v1"}))
            second = manuscripts.put("fictional-book", {"text": "v2"}, first["content_hash"])
            self.assertEqual(second["parent_hash"], first["content_hash"])
            with self.assertRaises(ContractError):
                manuscripts.put("fictional-book", {"text": "bad"}, "0" * 64)
            reviews = EditorialReviewStore(temporary)
            self.assertEqual(reviews.put("fictional-book", {"result": "FIX"})["version"], 1)

    def test_revision_requests_are_targeted(self):
        review = {
            "book_id": "fictional-book",
            "review_hash": "a" * 64,
            "findings": [{"code": "PACE_1", "section_ids": ["beat-2"], "excerpt": "bounded excerpt"}],
        }
        request = targeted_revision_request(review)
        self.assertEqual(request["finding_ids"], ["PACE_1"])
        self.assertEqual(request["affected_sections"], ["beat-2"])
        self.assertEqual(request["bounded_excerpts"], ["bounded excerpt"])

    def test_hash_stores_reject_forged_hashes_and_artifact_metadata_keeps_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(ContractError):
                DossierStore(temporary).put({"book_id": "x", "dossier_hash": "0" * 64})
            with self.assertRaises(ContractError):
                StoryPacketStore(temporary).put("x", {"packet_hash": "0" * 64})
            artifacts = ArtifactStore(temporary)
            one = artifacts.put(b"same", extension="txt", logical_id="one")
            two = artifacts.put(b"same", extension="txt", logical_id="two")
            self.assertNotEqual(one["id"], two["id"])
            self.assertEqual(one["sha256"], two["sha256"])

    def test_source_graph_unchanged_and_no_reachable_large_git_blob(self):
        graph_root = ROOT / "research" / "source-graph"
        before = tree_snapshot(graph_root)
        FactoryDirector(ROOT).evaluate_catalogue(False)
        self.assertEqual(before, tree_snapshot(graph_root))
        objects = subprocess.run(
            ["git", "rev-list", "--objects", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
        ).stdout.splitlines()
        object_ids = "\n".join(line.split(" ", 1)[0] for line in objects) + "\n"
        inspected = subprocess.run(
            ["git", "cat-file", "--batch-check=%(objecttype) %(objectsize)"],
            cwd=ROOT,
            input=object_ids,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
        for line in inspected:
            kind, size = line.split()
            if kind == "blob":
                self.assertLessEqual(int(size), 100 * 1024 * 1024)


if __name__ == "__main__":
    unittest.main()
