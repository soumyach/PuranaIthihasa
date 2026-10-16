import json
import tempfile
import unittest
from pathlib import Path

from book_factory.approvals import ApprovalStore
from book_factory.artifacts import ArtifactStore
from book_factory.budgets import BudgetGuard
from book_factory.catalogue import CatalogueStore
from book_factory.contracts import validate_named
from book_factory.director import FactoryDirector
from book_factory.errors import BudgetExceededError, ContractError, ProviderUnavailableError, TransitionError
from book_factory.locks import BookLease
from book_factory.providers.base import Provider, ProviderRegistry, guarded_provider_call
from book_factory.quality import (
    caption_dialogue_nonduplication,
    page_ordering,
    source_event_coverage,
    visual_evaluation_status,
)
from book_factory.source_graph import ReadOnlySourceGraph
from book_factory.state import StateStore, job_key, page_id
from book_factory.rules import rules_status
from book_factory.util import atomic_json_write, load_json, tree_snapshot


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = REPOSITORY_ROOT / "schemas" / "book-factory"


def catalogue(collections, books):
    return {"schema_version": "1.0", "collections": collections, "books": books}


def book(book_id, readiness="READY", priority=100, collection_ids=None):
    return {
        "id": book_id,
        "title": book_id,
        "line": "KATHAS",
        "readiness": readiness,
        "priority": priority,
        "collection_ids": collection_ids or [],
    }


class CatalogueTests(unittest.TestCase):
    def test_import_preserves_book_ids_and_collection_relationships(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = root / "catalogue.json"
            source = root / "incoming.json"
            atomic_json_write(destination, catalogue([], []))
            original = catalogue([{"id": "line-a", "title": "Line A"}], [book("original-007", collection_ids=["line-a"])])
            atomic_json_write(source, original)
            imported = CatalogueStore(destination).import_file(source)
            self.assertEqual(imported["books"][0]["id"], "original-007")
            self.assertEqual(imported["books"][0]["collection_ids"], ["line-a"])

    def test_source_incomplete_books_are_not_selected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "catalogue.json"
            atomic_json_write(path, catalogue([], [book("partial", "INCOMPLETE_SOURCE")]))
            self.assertIsNone(CatalogueStore(path).select_next())

    def test_ready_selection_is_deterministic(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "catalogue.json"
            atomic_json_write(path, catalogue([], [book("zeta", priority=1), book("alpha", priority=1), book("later", priority=2)]))
            store = CatalogueStore(path)
            self.assertEqual(store.select_next()["id"], "alpha")
            self.assertEqual(store.select_next(active_book_ids=["alpha"])["id"], "zeta")


class StateAndArtifactTests(unittest.TestCase):
    def test_state_persists_and_replays_after_interruption(self):
        with tempfile.TemporaryDirectory() as temporary:
            books = Path(temporary) / "books"
            store = StateStore(books, "book-a")
            store.initialize()
            expected = store.transition("SOURCE_CHECK", "op-source")
            store.state_path.unlink()
            recovered = StateStore(books, "book-a").load()
            self.assertEqual(recovered, expected)
            self.assertTrue(store.state_path.exists())

    def test_successful_operation_and_artifact_are_idempotent(self):
        with tempfile.TemporaryDirectory() as temporary:
            books = Path(temporary) / "books"
            store = StateStore(books, "book-a")
            store.initialize()
            first = store.transition("SOURCE_CHECK", "same-operation")
            second = store.transition("SOURCE_CHECK", "same-operation")
            self.assertEqual(first, second)
            self.assertEqual(len(store._events()), 2)
            artifacts = ArtifactStore(books)
            one = artifacts.put(b"same bytes", extension="txt")
            two = artifacts.put(b"same bytes", extension="txt")
            self.assertEqual(one, two)
            self.assertEqual(len(list((books / "_artifacts").rglob("*.txt"))), 1)

    def test_failed_stage_resumes_without_restarting_completed_stage(self):
        with tempfile.TemporaryDirectory() as temporary:
            store = StateStore(Path(temporary) / "books", "book-a")
            store.initialize()
            store.transition("SOURCE_CHECK", "advance-source")
            failed = store.transition("FAILED", "source-failed", recovery={"reason": "validator unavailable", "resume_stage": "SOURCE_CHECK"})
            self.assertEqual(failed["current_stage"], "FAILED")
            resumed = store.transition("SOURCE_CHECK", "resume-source")
            self.assertEqual(resumed["current_stage"], "SOURCE_CHECK")
            self.assertEqual(resumed["completed_stages"], ["QUEUED"])

    def test_illegal_transition_and_retry_limit_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            store = StateStore(Path(temporary) / "books", "book-a", max_retries=1)
            store.initialize()
            with self.assertRaises(TransitionError):
                store.transition("MANUSCRIPT", "skip")
            store.transition("SOURCE_CHECK", "advance")
            store.transition("FAILED", "fail", recovery={"reason": "test", "resume_stage": "SOURCE_CHECK"})
            store.transition("SOURCE_CHECK", "resume")
            with self.assertRaises(TransitionError):
                store.transition("FAILED", "fail-again", recovery={"reason": "test", "resume_stage": "SOURCE_CHECK"})

    def test_ids_and_job_keys_are_stable(self):
        self.assertEqual(page_id("book", 1), page_id("book", 1))
        first = job_key("book", "ILLUSTRATION", page_id("book", 1), ["b", "a"], ["p"], "1", "provider")
        second = job_key("book", "ILLUSTRATION", page_id("book", 1), ["a", "b"], ["p"], "1", "provider")
        self.assertEqual(first, second)


class ApprovalAndControlTests(unittest.TestCase):
    def test_approval_persists_and_exact_hash_is_respected(self):
        with tempfile.TemporaryDirectory() as temporary:
            store = ApprovalStore(temporary)
            record = store.create(
                "VISUAL_STYLE_OR_CHARACTER_FAMILY",
                "VISUAL_STYLE",
                "a" * 64,
                {"type": "collection", "id": "c1"},
                {"kind": "human", "id": "reviewer"},
                {"kind": "worker", "id": "creator"},
                "PASS",
                inheritance_allowed=True,
                invalidators=["rules_hash"],
            )
            found = ApprovalStore(temporary).find_valid("VISUAL_STYLE", "a" * 64, {"type": "book", "id": "b1", "ancestors": ["c1"]})
            self.assertEqual(found["id"], record["id"])
            self.assertIsNone(store.find_valid("VISUAL_STYLE", "b" * 64, {"type": "book", "id": "b1", "ancestors": ["c1"]}))
            self.assertIsNone(store.find_valid("VISUAL_STYLE", "a" * 64, {"type": "book", "id": "b1", "ancestors": ["c1"]}, ["rules_hash"]))

    def test_only_one_book_lease_can_be_active(self):
        with tempfile.TemporaryDirectory() as temporary:
            lease = BookLease(temporary)
            lease.acquire("book-a", "director-a")
            from book_factory.errors import LeaseError
            with self.assertRaises(LeaseError):
                lease.acquire("book-b", "director-b")
            lease.release("book-a", "director-a")


class CountingProvider(Provider):
    kind = "image"
    name = "counting-test-provider"

    def __init__(self):
        self.calls = 0

    def capabilities(self):
        return {"kind": self.kind, "name": self.name, "available": True, "network_calls": False}

    def estimate_minor_units(self, request):
        return request["estimate"]

    def execute(self, request, operation_key):
        self.calls += 1
        return {"status": "TEST_ONLY"}


class ProviderAndQualityTests(unittest.TestCase):
    def test_spending_cap_prevents_provider_execution(self):
        provider = CountingProvider()
        guard = BudgetGuard({"book_max_minor_units": 10, "page_max_minor_units": 10, "job_max_minor_units": 5, "max_retries": 0})
        with self.assertRaises(BudgetExceededError):
            guarded_provider_call(provider, {"estimate": 6}, "operation", guard, "page")
        self.assertEqual(provider.calls, 0)

    def test_missing_provider_is_an_honest_failure(self):
        registry = ProviderRegistry()
        with self.assertRaises(ProviderUnavailableError) as context:
            registry.require("visual_evaluation")
        self.assertIn("not configured", str(context.exception))

    def test_foundation_quality_results(self):
        self.assertEqual(source_event_coverage(["e1"], [], "book")["result"], "FIX")
        self.assertEqual(page_ordering([{"number": 2}], "book")["result"], "FIX")
        self.assertEqual(caption_dialogue_nonduplication([{"id": "p1", "captions": ["Same"], "dialogue": ["same"]}])["result"], "FIX")
        self.assertEqual(visual_evaluation_status("book")["result"], "ESCALATE")


class ContractAndDirectorTests(unittest.TestCase):
    def test_formal_contracts_reject_malformed_documents(self):
        for schema in ("book-manifest", "source-readiness", "manuscript", "bible", "page-script", "state", "event", "approval", "budget", "artifact", "qa-report", "worker-contract"):
            with self.subTest(schema=schema), self.assertRaises(ContractError):
                validate_named({}, SCHEMA_ROOT, schema)

    def test_worker_contracts_and_skill_frontmatter_are_machine_checkable(self):
        contracts = sorted((REPOSITORY_ROOT / "book-factory" / "contracts" / "workers").glob("*.json"))
        self.assertEqual(len(contracts), 6)
        for path in contracts:
            validate_named(load_json(path), SCHEMA_ROOT, "worker-contract")
        skills = sorted((REPOSITORY_ROOT / "skills").glob("book-factory-*/SKILL.md"))
        self.assertEqual(len(skills), 7)
        for path in skills:
            text = path.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"))
            frontmatter = text.split("---\n", 2)[1]
            fields = dict(line.split(": ", 1) for line in frontmatter.strip().splitlines())
            self.assertEqual(fields["name"], path.parent.name)
            self.assertTrue(fields["description"])

    def test_missing_rules_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            self.assertEqual(rules_status(temporary)["status"], "BLOCKED_STANDARD")

    def test_unimplemented_stage_cannot_be_marked_complete(self):
        with tempfile.TemporaryDirectory() as temporary:
            books = Path(temporary) / "books"
            books.mkdir()
            atomic_json_write(books / "catalogue.json", catalogue([], [book("book-a")]))
            state_store = StateStore(books, "book-a")
            before = state_store.initialize()
            director = FactoryDirector(REPOSITORY_ROOT)
            director.books_root = books
            director.catalogue = CatalogueStore(books / "catalogue.json")
            result = director.resume("book-a")
            after = state_store.load()
            self.assertEqual(result["status"], "NOT_IMPLEMENTED")
            self.assertEqual(before, after)


class SourceGraphTests(unittest.TestCase):
    def test_adapter_reads_without_modifying_graph(self):
        graph_root = REPOSITORY_ROOT / "research" / "source-graph"
        before = tree_snapshot(graph_root)
        adapter = ReadOnlySourceGraph(graph_root)
        report = adapter.verify()
        spines = adapter.complete_story_spines()
        packet = adapter.story_packet(spines[0]["id"])
        after = tree_snapshot(graph_root)
        self.assertTrue(report["passed"])
        self.assertEqual(before, after)
        self.assertEqual(packet["spine"]["id"], spines[0]["id"])
        self.assertEqual([item["sequence"] for item in packet["events"]], sorted(item["sequence"] for item in packet["events"]))
        self.assertTrue(packet["completeness"]["not_exhaustive_scripture_verification"])


if __name__ == "__main__":
    unittest.main()
