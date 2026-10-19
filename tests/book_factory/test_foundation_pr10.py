import unittest
from pathlib import Path

from book_factory.approvals import ApprovalStore
from book_factory.director import FactoryDirector
from book_factory.errors import ContractError
from book_factory.orchestration import validate_reference_receipt
from book_factory.production_integration import (
    BOOK_ID,
    REVIEW_DIMENSIONS,
    SELECTED_PAGE_IDS,
    RealProductionSlice,
    validate_real_image_review,
)
from book_factory.util import content_hash, load_json, sha256_bytes, tree_snapshot


ROOT = Path(__file__).resolve().parents[2]


class PR10RealProductionIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manager = RealProductionSlice(ROOT)
        cls.prepared = cls.manager.prepare()
        cls.plan_record = load_json(ROOT / "books" / BOOK_ID / "production-slices" / "v0001.json")
        cls.plan = cls.plan_record["payload"]

    def test_01_real_input_asset_hashes_are_recomputed(self):
        self.assertGreaterEqual(len(self.plan["locked_inputs"]), 12)
        for asset in self.plan["locked_inputs"]:
            path = ROOT / asset["path"]
            self.assertTrue(path.is_file(), asset["path"])
            self.assertEqual(sha256_bytes(path.read_bytes()), asset["sha256"])

    def test_02_two_exact_storyboard_pages_are_selected(self):
        self.assertEqual(tuple(item["page_id"] for item in self.plan["selected_pages"]), SELECTED_PAGE_IDS)
        self.assertEqual([item["page_number"] for item in self.plan["selected_pages"]], [1, 4])
        self.assertEqual(self.plan["selection_evidence"]["storyboard_page_count"], 32)
        self.assertFalse(self.plan["selection_evidence"]["replacement_scenes_invented"])

    def test_03_dialogue_page_preserves_characters_event_and_layout(self):
        page = self.plan["selected_pages"][0]
        self.assertEqual(page["event_ids"], ["dm-event-008"])
        self.assertEqual(page["layout"]["type"], "TWO_PANEL")
        self.assertTrue({"dm-medhas", "dm-suratha", "dm-samadhi"}.issubset(page["character_ids"]))
        self.assertEqual(page["panel_ids"], ["p01-panel-01", "p01-panel-02"])

    def test_04_manifestation_page_preserves_source_event_and_full_page_layout(self):
        page = self.plan["selected_pages"][1]
        self.assertEqual(page["event_ids"], ["dm-event-009"])
        self.assertEqual(page["layout"]["type"], "FULL_PAGE")
        self.assertEqual(page["panel_ids"], ["p04-panel-01"])
        self.assertIn("dm-devi", page["character_ids"])

    def test_05_exact_lettering_is_byte_for_byte_from_page_scripts(self):
        for selected in self.plan["selected_pages"]:
            source = load_json(ROOT / selected["page_script"]["path"])
            self.assertEqual(selected["lettering"], source["lettering"])
            self.assertEqual(selected["lettering_hash"], content_hash(source["lettering"]))

    def test_06_reference_packages_bind_actual_a_b_and_available_d_pixels(self):
        for page in self.plan["selected_pages"]:
            request = {"references": page["references"]}
            submitted = [
                {"role": item["role"], "sha256": item["sha256"], "path": item["path"]}
                for item in page["references"] if item["available"]
            ]
            result = validate_reference_receipt(request, {
                "provider_capabilities": {"reference_images": True},
                "submitted_references": submitted,
            })
            self.assertTrue(result["reference_conditioned"])
            for item in page["references"]:
                if item["available"]:
                    self.assertEqual(sha256_bytes((ROOT / item["path"]).read_bytes()), item["sha256"])

    def test_07_missing_campaign_authorization_blocks_generation(self):
        self.assertEqual(self.plan["authorization"]["status"], "NOT_GRANTED")
        self.assertFalse(self.manager.status()["run"]["generation_authorized"])
        with self.assertRaises(ContractError):
            self.manager.prepare_generation(SELECTED_PAGE_IDS[0])

    def test_08_operation_ceiling_and_zero_cost_do_not_imply_authorization(self):
        subject = self.plan["authorization_subject"]
        self.assertEqual(subject["operation_ceiling_total"], 2)
        self.assertEqual(subject["operation_ceiling_per_page"], 1)
        self.assertEqual(subject["maximum_paid_spend_minor_units"], 0)
        self.assertFalse(self.plan["authorization"]["proposed_operation_ceiling_is_authorization"])
        self.assertTrue(self.plan["cost_policy"]["no_cost_capability_still_requires_campaign_authorization"])

    def test_09_backend_exposes_actual_reference_path_interface_but_is_host_scoped(self):
        backend = self.plan["backend"]
        self.assertTrue(backend["reference_conditioning"])
        self.assertEqual(backend["reference_input_interface"], "referenced_image_paths")
        self.assertFalse(backend["repository_programmatic_invocation"])

    def _review_request(self):
        return {
            "book_id": BOOK_ID,
            "page_id": SELECTED_PAGE_IDS[0],
            "image_sha256": "a" * 64,
            "producer_ids": ["producer"],
        }

    def _review_response(self, reviewer_id="reviewer", pixels=True):
        return {
            "image_sha256": "a" * 64,
            "reviewer": {
                "id": reviewer_id,
                "image_capable": True,
                "inspected_actual_pixels": pixels,
                "reading_size": "ACTUAL_READING_SIZE",
            },
            "assessments": [
                {"dimension": dimension, "result": "PASS", "evidence": "fixture validator evidence"}
                for dimension in REVIEW_DIMENSIONS
            ],
            "findings": [],
        }

    def test_10_image_producer_cannot_approve_own_artwork(self):
        result = validate_real_image_review(self._review_request(), self._review_response("producer"))
        self.assertEqual(result["result"], "ESCALATE")
        self.assertEqual(result["code"], "REVIEWER_NOT_INDEPENDENT_FROM_PRODUCER")

    def test_11_no_actual_pixel_inspection_means_no_semantic_pass(self):
        result = validate_real_image_review(self._review_request(), self._review_response(pixels=False))
        self.assertEqual(result["result"], "ESCALATE")
        self.assertEqual(result["code"], "ACTUAL_PIXEL_REVIEW_NOT_EXECUTED")

    def test_12_complete_independent_review_contract_can_pass_validation_only(self):
        result = validate_real_image_review(self._review_request(), self._review_response())
        self.assertEqual(result["result"], "PASS")
        self.assertTrue(result["independent_actual_pixel_review"])

    def test_13_localized_recovery_is_isolated_and_preserves_other_pages(self):
        result = self.manager.validate()["isolated_recovery"]
        self.assertEqual(result["invalidate_scope"], "PAGE_LOCAL")
        self.assertTrue(result["preserve_other_pages"])
        self.assertTrue(result["preserve_prior_versions"])
        self.assertFalse(result["reset_retry_counter"])

    def test_14_preview_production_and_pdf_gates_remain_isolated(self):
        gates = self.plan["artifact_gates"]
        self.assertIn("BLOCKED", gates["composition"])
        self.assertEqual(gates["independent_visual_review"], "NOT_EXECUTED_NO_NEW_PIXELS")
        self.assertEqual(gates["pdf"], "NOT_CREATED_ART_AND_REVIEW_GATES_BLOCKED")
        self.assertFalse(self.plan["publication_eligible"])

    def test_15_persisted_execution_state_is_idempotent(self):
        repeated = self.manager.prepare()
        self.assertFalse(repeated["mutated"])
        self.assertEqual(repeated["run"]["actual_image_operations"], 0)
        self.assertEqual(repeated["run"]["actual_cost_minor_units"], 0)
        self.assertEqual(len(list((ROOT / "books" / BOOK_ID / "production-slices").glob("v*.json"))), 1)
        self.assertEqual(len(list((ROOT / "books" / BOOK_ID / "production-campaign-requests").glob("v*.json"))), 1)

    def test_16_one_director_invocation_stops_at_exact_real_blocker(self):
        result = FactoryDirector(ROOT).produce_book(BOOK_ID)
        self.assertEqual(result["status"], "ESCALATE")
        self.assertFalse(result["mutated_art"])
        self.assertEqual(result["run"]["status"], "AWAITING_CAMPAIGN_AUTHORIZATION")
        self.assertEqual(result["run"]["manual_interventions_currently_required"], 1)

    def test_17_queue_continuation_and_dm08_exclusion_are_preserved(self):
        queue = FactoryDirector(ROOT).factory_queue()
        rows = {item["book_id"]: item for item in queue["entries"]}
        self.assertEqual(rows["DM08"]["queue_status"], "EXCLUDED")
        self.assertFalse(rows["DM08"]["private_production_eligible"])
        self.assertFalse(self.plan["continuous_book_readiness"]["next_book_started"])

    def test_18_campaign_approval_is_non_inheritable(self):
        with self.assertRaises(ContractError):
            ApprovalStore("/tmp/pr10-non-inheritable-unused").create(
                "PRODUCTION_CAMPAIGN", "PRODUCTION_CAMPAIGN", "b" * 64,
                {"type": "book", "id": BOOK_ID},
                {"id": "human"}, {"id": "director"}, "PASS", inheritance_allowed=True,
            )

    def test_19_source_graph_and_dm08_remain_unchanged_by_idempotent_prepare(self):
        graph_before = tree_snapshot(ROOT / "research" / "source-graph")
        dm08_before = tree_snapshot(ROOT / "books" / "DM08")
        self.manager.prepare()
        self.assertEqual(graph_before, tree_snapshot(ROOT / "research" / "source-graph"))
        self.assertEqual(dm08_before, tree_snapshot(ROOT / "books" / "DM08"))

    def test_20_pr6_attempts_remain_exhausted_without_counter_reset(self):
        history = self.plan["pr6_history"]
        self.assertEqual(history["attempts_used_total"], history["attempts_allowed_total"])
        self.assertTrue(history["retry_ceiling_exhausted"])
        self.assertFalse(history["counter_reset"])


if __name__ == "__main__":
    unittest.main()
