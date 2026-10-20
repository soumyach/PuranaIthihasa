import copy
import json
import tempfile
import unittest
from pathlib import Path

from book_factory.approvals import ApprovalStore
from book_factory.catalogue import CatalogueStore
from book_factory.director import FactoryDirector
from book_factory.errors import BudgetExceededError, ContractError
from book_factory.orchestration import (
    JobLedger,
    route_page_repair,
    validate_composed_page_review,
    validate_reference_receipt,
)
from book_factory.util import atomic_json_write, content_hash, load_json, tree_snapshot


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = ROOT / "book-factory" / "fixtures" / "autonomous-orchestration"


def worker(identity="worker"):
    return {"id": identity, "role": identity, "version": "test-1"}


def receipt(identity="worker"):
    return {"mechanism": "UNIT_TEST", "executed_by": identity}


def finish_pass(ledger, record, output="a" * 64):
    return ledger.finish(record, "PASS", [output], receipt(record["worker_identity"]["id"]), 0)


class PR9QueueAndJobTests(unittest.TestCase):
    def fixture_director(self, temporary):
        return FactoryDirector(
            ROOT,
            FIXTURE_ROOT / "catalogue.json",
            Path(temporary) / "runtime",
        )

    def test_01_deterministic_selection_skips_blocked_and_excludes_dm08(self):
        with tempfile.TemporaryDirectory() as temporary:
            queue = self.fixture_director(temporary).factory_queue(True)
            self.assertEqual(queue["selected_book"], "FX-001")
            rows = {row["book_id"]: row for row in queue["entries"]}
            self.assertEqual(rows["FX-BLOCKED"]["queue_status"], "BLOCKED")
            self.assertEqual(rows["DM08"]["queue_status"], "EXCLUDED")
            self.assertFalse(rows["DM08"]["private_production_eligible"])

    def test_02_dependency_blocks_then_queue_continues(self):
        with tempfile.TemporaryDirectory() as temporary:
            director = self.fixture_director(temporary)
            before = {row["book_id"]: row for row in director.factory_queue(True)["entries"]}
            self.assertIn("DEPENDENCIES_NOT_READY", before["FX-002"]["reasons"])
            director.produce_book("FX-001", True, FIXTURE_ROOT / "lifecycle-plan.json")
            director.resume_book("FX-001", True, FIXTURE_ROOT / "lifecycle-plan.json")
            after = director.factory_queue(True)
            self.assertEqual(after["selected_book"], "FX-002")

    def test_03_stage_prerequisites_reject_incomplete_fixture_plan(self):
        with tempfile.TemporaryDirectory() as temporary:
            director = self.fixture_director(temporary)
            plan = load_json(FIXTURE_ROOT / "lifecycle-plan.json")
            plan["stages"].pop("EDITORIAL_QA")
            path = Path(temporary) / "bad-plan.json"
            atomic_json_write(path, plan)
            with self.assertRaises(ContractError):
                director.produce_book("FX-001", True, path)

    def test_04_durable_interruption_resume_reuses_stable_job_and_attempt(self):
        with tempfile.TemporaryDirectory() as temporary:
            director = self.fixture_director(temporary)
            first = director.produce_book("FX-001", True, FIXTURE_ROOT / "lifecycle-plan.json")
            self.assertEqual(first["status"], "INTERRUPTED")
            interrupted = next(job for job in first["jobs"] if job["stage"] == "ILLUSTRATION")
            second = director.resume_book("FX-001", True, FIXTURE_ROOT / "lifecycle-plan.json")
            completed = next(job for job in second["jobs"] if job["stage"] == "ILLUSTRATION")
            self.assertEqual(second["status"], "FIXTURE_LIFECYCLE_COMPLETE")
            self.assertEqual(interrupted["job_id"], completed["job_id"])
            self.assertEqual(completed["attempt_number"], 1)
            self.assertEqual(completed["result"], "PASS")

    def test_05_completed_stage_is_idempotently_reused(self):
        with tempfile.TemporaryDirectory() as temporary:
            director = self.fixture_director(temporary)
            director.produce_book("FX-001", True, FIXTURE_ROOT / "lifecycle-plan.json")
            completed = director.resume_book("FX-001", True, FIXTURE_ROOT / "lifecycle-plan.json")
            events = len(JobLedger(Path(temporary) / "runtime" / "fixture-books", "FX-001", True).events())
            repeated = director.resume_book("FX-001", True, FIXTURE_ROOT / "lifecycle-plan.json")
            self.assertEqual(repeated["status"], "FIXTURE_LIFECYCLE_COMPLETE")
            self.assertEqual(len(JobLedger(Path(temporary) / "runtime" / "fixture-books", "FX-001", True).events()), events)
            self.assertTrue(repeated["trace"][0]["reused"])
            self.assertFalse(completed["publication_eligible"])

    def test_06_input_change_invalidates_only_stage_and_dependents(self):
        with tempfile.TemporaryDirectory() as temporary:
            ledger = JobLedger(Path(temporary) / "books", "B1")
            source, _ = ledger.begin("SOURCE_CHECK", ["source-v1"], ["policy"], worker("source"))
            finish_pass(ledger, source, "1" * 64)
            manuscript, _ = ledger.begin("MANUSCRIPT", ["1" * 64], ["policy"], worker("writer"))
            finish_pass(ledger, manuscript, "2" * 64)
            changed, _ = ledger.begin("SOURCE_CHECK", ["source-v2"], ["policy"], worker("source"))
            jobs = {job["job_id"]: job for job in ledger.jobs()}
            self.assertEqual(jobs[source["job_id"]]["status"], "INVALIDATED")
            self.assertEqual(jobs[manuscript["job_id"]]["status"], "INVALIDATED")
            self.assertEqual(changed["status"], "RUNNING")

    def test_07_attempt_budget_does_not_reset_after_fix(self):
        with tempfile.TemporaryDirectory() as temporary:
            ledger = JobLedger(Path(temporary) / "books", "B1")
            first, _ = ledger.begin("ILLUSTRATION", ["v1"], [], worker("artist"), max_attempts=1)
            ledger.finish(first, "FIX", [], receipt("artist"), 0, {"action": "TARGETED_REPAIR"})
            with self.assertRaises(BudgetExceededError):
                ledger.begin("ILLUSTRATION", ["v2"], [], worker("artist"), max_attempts=1)

    def test_08_fixture_budget_blocks_any_nonzero_spend(self):
        with tempfile.TemporaryDirectory() as temporary:
            director = self.fixture_director(temporary)
            plan = load_json(FIXTURE_ROOT / "lifecycle-plan.json")
            plan["stages"]["SOURCE_CHECK"]["estimated_cost_minor_units"] = 1
            path = Path(temporary) / "paid-plan.json"
            atomic_json_write(path, plan)
            with self.assertRaises(BudgetExceededError):
                director.produce_book("FX-001", True, path)


class PR9ApprovalAndQualityTests(unittest.TestCase):
    def test_09_bounded_approval_inheritance_and_hash_invalidation(self):
        with tempfile.TemporaryDirectory() as temporary:
            store = ApprovalStore(temporary)
            approval = store.create(
                "LOCATION_REFERENCE", "LOCATION", "a" * 64,
                {"type": "location", "id": "city-a"},
                {"id": "human"}, {"id": "artist"}, "PASS",
                inheritance_allowed=True, invalidators=["reference_hash"],
                source_scope="scope", tradition_id="tradition", edition_id="edition",
            )
            valid = store.find_valid(
                "LOCATION", "a" * 64,
                {"type": "book", "id": "book-a", "ancestors": ["city-a"]},
                target_context={"source_scope": "scope", "tradition_id": "tradition", "edition_id": "edition"},
            )
            self.assertEqual(valid["id"], approval["id"])
            self.assertIsNone(store.find_valid(
                "LOCATION", "a" * 64,
                {"type": "book", "id": "book-a", "ancestors": ["city-a"]},
                current_invalidators=["reference_hash"],
                target_context={"source_scope": "scope", "tradition_id": "tradition", "edition_id": "edition"},
            ))

    def test_10_page_repair_is_local_and_preserves_attempts(self):
        route = route_page_repair({"code": "TEXT_OVERFLOW", "page_id": "page-18", "panel_id": "panel-2"})
        self.assertEqual(route["repair_type"], "LETTERING_REPAIR")
        self.assertEqual(route["invalidate_scope"], "PAGE_LOCAL")
        self.assertTrue(route["preserve_other_pages"])
        self.assertFalse(route["reset_retry_counter"])

    def test_11_semantic_pass_requires_actual_image_capability(self):
        request = {"rendered_page_hash": "a" * 64, "creator_ids": ["composer"], "gold_standard_hashes": ["b" * 64]}
        response = {
            "rendered_page_hash": "a" * 64,
            "reviewer": {"id": "reviewer", "image_capable": False, "inspected_actual_pixels": False},
            "assessments": {}, "findings": [],
        }
        result = validate_composed_page_review(request, response)
        self.assertEqual(result["result"], "ESCALATE")

    def test_12_no_false_artistic_pass_or_self_review(self):
        request = {"rendered_page_hash": "a" * 64, "creator_ids": ["composer"], "gold_standard_hashes": ["b" * 64]}
        response = {
            "rendered_page_hash": "a" * 64,
            "reviewer": {"id": "composer", "image_capable": True, "inspected_actual_pixels": True, "reading_size": "ACTUAL_READING_SIZE"},
            "assessments": {
                "mechanical": [{"result": "PASS"}],
                "semantic": [{"result": "PASS"}],
                "artistic_comparison": [{"result": "PASS"}],
            },
            "findings": [],
        }
        self.assertEqual(validate_composed_page_review(request, response)["result"], "ESCALATE")

    def test_13_valid_independent_composed_page_review_passes(self):
        request = {"rendered_page_hash": "a" * 64, "creator_ids": ["composer"], "gold_standard_hashes": ["b" * 64]}
        response = {
            "rendered_page_hash": "a" * 64,
            "reviewer": {"id": "independent-reviewer", "image_capable": True, "inspected_actual_pixels": True, "reading_size": "ACTUAL_READING_SIZE"},
            "assessments": {
                "mechanical": [{"result": "PASS"}],
                "semantic": [{"result": "PASS"}],
                "artistic_comparison": [{"result": "PASS"}],
            },
            "findings": [],
        }
        result = validate_composed_page_review(request, response)
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["gold_standard_hashes"], ["b" * 64])

    def test_14_reference_receipt_integrity_and_no_text_only_mislabel(self):
        request = {"references": [
            {"role": "REFERENCE_A_SERIES_VISUAL_IDENTITY", "sha256": "a" * 64, "path": "a.png", "available": True},
            {"role": "REFERENCE_B_PAGE_COMPOSITION", "sha256": "b" * 64, "path": "b.png", "available": True},
            {"role": "REFERENCE_C_CHARACTER_IDENTITY", "available": False},
            {"role": "REFERENCE_D_SETTING_ENVIRONMENT", "available": False},
        ]}
        unsupported = {"provider_capabilities": {"reference_images": False}, "submitted_references": []}
        self.assertFalse(validate_reference_receipt(request, unsupported)["reference_conditioned"])
        exact = {
            "provider_capabilities": {"reference_images": True},
            "submitted_references": [
                {"role": "REFERENCE_A_SERIES_VISUAL_IDENTITY", "sha256": "a" * 64, "path": "a.png"},
                {"role": "REFERENCE_B_PAGE_COMPOSITION", "sha256": "b" * 64, "path": "b.png"},
            ],
        }
        self.assertTrue(validate_reference_receipt(request, exact)["reference_conditioned"])
        forged = copy.deepcopy(exact)
        forged["submitted_references"][0]["sha256"] = "c" * 64
        with self.assertRaises(ContractError):
            validate_reference_receipt(request, forged)


class PR9EndToEndTests(unittest.TestCase):
    def test_15_complete_synthetic_lifecycle_pdf_lettering_artifacts_and_isolation(self):
        before_graph = tree_snapshot(ROOT / "research" / "source-graph")
        before_dm04 = tree_snapshot(ROOT / "books" / "DM04")
        with tempfile.TemporaryDirectory() as temporary:
            director = FactoryDirector(ROOT, FIXTURE_ROOT / "catalogue.json", Path(temporary) / "runtime")
            first = director.produce_next(False, True, FIXTURE_ROOT / "lifecycle-plan.json")
            self.assertEqual(first["status"], "INTERRUPTED")
            result = director.resume_book("FX-001", True, FIXTURE_ROOT / "lifecycle-plan.json")
            self.assertEqual(result["status"], "FIXTURE_LIFECYCLE_COMPLETE")
            self.assertFalse(result["publication_eligible"])
            self.assertEqual(result["run"]["dimensions"]["editorial_certification"], "PASS_FIXTURE_ONLY_INDEPENDENT")
            self.assertEqual(result["run"]["dimensions"]["publication_clearance"], "BLOCKED")
            jobs = {job["stage"]: job for job in result["jobs"]}
            self.assertEqual(set(jobs), set(load_json(FIXTURE_ROOT / "lifecycle-plan.json")["stages"]))
            self.assertEqual(len(jobs["EDITORIAL_QA"]["worker_identity"]["reviewer_ids"]), 2)
            self.assertNotIn("fixture-manuscript-specialist", jobs["EDITORIAL_QA"]["worker_identity"]["reviewer_ids"])
            self.assertTrue(all(job["cost"]["actual_minor_units"] == 0 for job in jobs.values()))
            artifact_root = Path(temporary) / "runtime" / "fixture-books" / "_artifacts" / "sha256"
            lettering_hash = jobs["LETTERING"]["output_hashes"][0]
            lettering = load_json(artifact_root / lettering_hash[:2] / (lettering_hash + ".json"))
            expected_text = load_json(FIXTURE_ROOT / "lifecycle-plan.json")["exact_lettering"]
            self.assertEqual(lettering["exact_lettering"], expected_text)
            pdf_hash = jobs["PDF_LAYOUT"]["output_hashes"][0]
            pdf_record = load_json(artifact_root / pdf_hash[:2] / (pdf_hash + ".json"))
            self.assertEqual(pdf_record["pdf"]["inspection_result"], "PASS")
            self.assertEqual(pdf_record["pdf"]["page_count"], 4)
            self.assertTrue(Path(pdf_record["pdf"]["path"]).is_file())
            costs = director.factory_costs(True)
            self.assertEqual(costs["actual_minor_units"], 0)
            self.assertEqual(costs["paid_calls_executed"], 0)
        self.assertEqual(before_graph, tree_snapshot(ROOT / "research" / "source-graph"))
        self.assertEqual(before_dm04, tree_snapshot(ROOT / "books" / "DM04"))

    def test_16_provider_failure_stops_without_false_success(self):
        with tempfile.TemporaryDirectory() as temporary:
            director = FactoryDirector(ROOT, FIXTURE_ROOT / "catalogue.json", Path(temporary) / "runtime")
            plan = load_json(FIXTURE_ROOT / "lifecycle-plan.json")
            plan["stages"]["ART_PROOFS"] = {
                "worker_id": "unavailable-fixture-provider",
                "result": "ESCALATE",
                "recovery": {"action": "CONFIGURE_APPROVED_PROVIDER", "reason": "provider unavailable"}
            }
            path = Path(temporary) / "provider-failure.json"
            atomic_json_write(path, plan)
            result = director.produce_book("FX-001", True, path)
            self.assertEqual(result["status"], "ESCALATE")
            self.assertEqual(result["run"]["current_stage"], "ART_PROOFS")
            art_job = next(job for job in result["jobs"] if job["stage"] == "ART_PROOFS")
            self.assertEqual(art_job["result"], "ESCALATE")
            self.assertFalse(art_job["execution_receipt"]["real_provider_call"])

    def test_17_actual_dm04_reports_completed_pr11_without_mutating_pr6_art(self):
        with tempfile.TemporaryDirectory() as temporary:
            before = tree_snapshot(ROOT / "books" / "DM04" / "illustration-proofs")
            director = FactoryDirector(ROOT, orchestration_runtime_root=Path(temporary) / "runtime")
            result = director.produce_book("DM04")
            codes = {item["code"] for item in result["run"]["blocked"]}
            self.assertEqual(result["status"], "REVIEWED_FIX_REQUIRED_CAMPAIGN_COMPLETE_NO_RETRY")
            self.assertIn("PR11_INDEPENDENT_VISUAL_REVIEW_FIX", codes)
            self.assertIn("PR11_INDEPENDENT_VISUAL_REVIEW_ESCALATE", codes)
            self.assertEqual(result["run"]["actual_image_operations"], 2)
            self.assertFalse(result["mutated_art"])
            self.assertEqual(before, tree_snapshot(ROOT / "books" / "DM04" / "illustration-proofs"))

    def test_18_cli_surface_is_registered(self):
        from book_factory.cli import build_parser
        parser = build_parser()
        for argv in (
            ["produce-book", "--book-id", "FX-001"],
            ["resume-book", "--book-id", "FX-001"],
            ["queue"], ["blocked"], ["approvals"], ["costs"], ["status"],
        ):
            self.assertEqual(parser.parse_args(argv).command, argv[0])

    def test_19_source_graph_is_immutable_under_queue_and_status(self):
        before = tree_snapshot(ROOT / "research" / "source-graph")
        director = FactoryDirector(ROOT)
        self.assertEqual(director.factory_queue()["catalogue_count"], 78)
        self.assertEqual(director.orchestrator.status()["implementation"], "FOUNDATION_PR9")
        self.assertEqual(before, tree_snapshot(ROOT / "research" / "source-graph"))

    def test_20_publication_gate_never_equates_fixture_completion_with_clearance(self):
        with tempfile.TemporaryDirectory() as temporary:
            director = FactoryDirector(ROOT, FIXTURE_ROOT / "catalogue.json", Path(temporary) / "runtime")
            director.produce_book("FX-001", True, FIXTURE_ROOT / "lifecycle-plan.json")
            result = director.resume_book("FX-001", True, FIXTURE_ROOT / "lifecycle-plan.json")
            self.assertEqual(result["run"]["current_stage"], "READY_FOR_PUBLICATION")
            self.assertFalse(result["run"]["publication_eligible"])
            self.assertEqual(result["run"]["dimensions"]["publication_clearance"], "BLOCKED")
            queue = director.factory_queue(True)
            row = next(item for item in queue["entries"] if item["book_id"] == "FX-001")
            self.assertFalse(row["public_publication_eligible"])


if __name__ == "__main__":
    unittest.main()
