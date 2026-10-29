import unittest
from pathlib import Path

from book_factory.director import FactoryDirector
from book_factory.errors import ContractError
from book_factory.illustration_production import inspect_png
from book_factory.production_integration import (
    BOOK_ID,
    REVIEW_DIMENSIONS,
    SELECTED_PAGE_IDS,
    RealProductionSlice,
)
from book_factory.util import load_json, sha256_bytes, tree_snapshot


ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN_SUBJECT = "5a5b7c2a606f47a9b72ef001f19ef9c8736f4b328d2434dae08c5d0b08c061d7"
IMAGE_HASHES = {
    SELECTED_PAGE_IDS[0]: "5a8d154988f7f9b67ff927ab8b3d4e8b9fe96e6d7a0c99be4d3da9ef6fbdecf7",
    SELECTED_PAGE_IDS[1]: "cfac6ab6666e84fcd79d1fccd1aa5273adf4e28185d823cd92847131b7802819",
}
EXPECTED_RESULTS = {
    SELECTED_PAGE_IDS[0]: "FIX",
    SELECTED_PAGE_IDS[1]: "ESCALATE",
}


class PR11ControlledVisualPilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manager = RealProductionSlice(ROOT)
        cls.status = cls.manager.status()["run"]

    def _record(self, kind, page_id):
        path = ROOT / "books" / BOOK_ID / kind / page_id / "v0001.json"
        self.assertTrue(path.is_file(), path)
        return load_json(path)

    def test_01_exact_campaign_completed_at_two_operations(self):
        self.assertEqual(self.status["status"], "REVIEWED_FIX_REQUIRED_CAMPAIGN_COMPLETE_NO_RETRY")
        self.assertEqual(self.status["actual_image_operations"], 2)
        self.assertEqual(self.status["authorized_image_operation_ceiling"], 2)
        self.assertEqual(set(self.status["image_hashes"]), set(SELECTED_PAGE_IDS))

    def test_02_images_are_real_valid_locked_canvas_pixels(self):
        for page_id, expected_hash in IMAGE_HASHES.items():
            receipt = self._record("production-image-receipts", page_id)["payload"]
            image = inspect_png(ROOT / receipt["image"]["path"])
            self.assertEqual(image["sha256"], expected_hash)
            self.assertEqual((image["width"], image["height"]), (1086, 1448))
            self.assertEqual(image["integrity"], "PASS_CRC_AND_PIXEL_STREAM")

    def test_03_receipts_bind_exact_campaign_request_and_builtin_tool(self):
        for page_id in SELECTED_PAGE_IDS:
            receipt = self._record("production-image-receipts", page_id)["payload"]
            provider = receipt["provider"]
            self.assertEqual(receipt["campaign_subject_hash"], CAMPAIGN_SUBJECT)
            self.assertEqual(provider["provider_id"], "codex-built-in-image-gen")
            self.assertEqual(provider["host_tool"], "image_gen.imagegen")
            self.assertFalse(provider["api_key_supplied"])
            self.assertFalse(provider["external_provider_authorization_requested"])
            self.assertFalse(provider["paid_billing_requested"])
            self.assertTrue(receipt["reference_validation"]["reference_conditioned"])

    def test_04_submitted_reference_hashes_recompute_from_actual_files(self):
        for page_id in SELECTED_PAGE_IDS:
            receipt = self._record("production-image-receipts", page_id)["payload"]
            for reference in receipt["provider"]["submitted_references"]:
                self.assertEqual(
                    sha256_bytes((ROOT / reference["path"]).read_bytes()), reference["sha256"]
                )

    def test_05_missing_reference_roles_remain_explicitly_unavailable(self):
        manifestation = self._record("production-image-receipts", SELECTED_PAGE_IDS[1])["payload"]
        roles = {item["role"] for item in manifestation["provider"]["submitted_references"]}
        self.assertEqual(roles, {
            "REFERENCE_A_SERIES_VISUAL_IDENTITY", "REFERENCE_B_PAGE_COMPOSITION",
        })
        request = self._record("production-generation-requests", SELECTED_PAGE_IDS[1])["payload"]
        unavailable = {item["role"] for item in request["references"] if not item["available"]}
        self.assertEqual(unavailable, {
            "REFERENCE_C_CHARACTER_IDENTITY", "REFERENCE_D_SETTING_ENVIRONMENT",
        })

    def test_06_cost_is_unknown_not_falsely_recorded_as_zero(self):
        self.assertIsNone(self.status["actual_cost_minor_units"])
        self.assertEqual(
            self.status["actual_cost_status"],
            "UNKNOWN_TOOL_INTERFACE_DOES_NOT_EXPOSE_INCREMENTAL_USD",
        )
        costs = FactoryDirector(ROOT).factory_costs()
        self.assertIsNone(costs["actual_minor_units"])
        self.assertEqual(costs["paid_calls_executed"], 0)
        self.assertEqual(self.status["purchased_credit_balance_observed"], "0")

    def test_07_reviews_are_independent_actual_pixel_reviews(self):
        for page_id, expected in EXPECTED_RESULTS.items():
            review = self._record("production-visual-reviews", page_id)["payload"]
            self.assertEqual(review["result"], expected)
            self.assertTrue(review["independent_actual_pixel_review"])
            self.assertNotIn(review["reviewer"]["id"], {"/root"})
            self.assertTrue(review["reviewer"]["image_capable"])
            self.assertTrue(review["reviewer"]["inspected_actual_pixels"])
            self.assertEqual(review["reviewer"]["reading_size"], "ACTUAL_READING_SIZE")
            self.assertEqual([item["dimension"] for item in review["assessments"]], list(REVIEW_DIMENSIONS))

    def test_08_nonpass_reviews_generate_nonexecuting_correction_requests(self):
        for page_id, expected in EXPECTED_RESULTS.items():
            correction = self._record("production-correction-requests", page_id)["payload"]
            self.assertEqual(correction["result"], expected)
            self.assertFalse(correction["generation_retry_authorized"])
            self.assertEqual(correction["remaining_campaign_image_operations"], 0)
            self.assertFalse(correction["pr6_counter_reset"])
            self.assertTrue(correction["localized_findings"])

    def test_09_no_retry_can_be_prepared(self):
        for page_id in SELECTED_PAGE_IDS:
            with self.assertRaises(ContractError):
                self.manager.prepare_generation(page_id)

    def test_10_preview_and_pdf_gates_remain_closed(self):
        self.assertEqual(self.status["composition"], "NOT_CREATED")
        self.assertEqual(self.status["pdf"], "NOT_CREATED_ART_AND_REVIEW_GATES_BLOCKED")
        self.assertFalse(self.status["publication_eligible"])
        self.assertFalse(any((ROOT / "books" / BOOK_ID / "production-pilot").glob("**/*.pdf")))

    def test_11_pr6_attempt_history_was_not_reset(self):
        plan = load_json(ROOT / "books" / BOOK_ID / "production-slices" / "v0001.json")["payload"]
        history = plan["pr6_history"]
        self.assertEqual(history["attempts_used_total"], history["attempts_allowed_total"])
        self.assertTrue(history["retry_ceiling_exhausted"])
        self.assertFalse(history["counter_reset"])

    def test_12_read_only_status_preserves_source_graph_and_dm08(self):
        graph_before = tree_snapshot(ROOT / "research" / "source-graph")
        dm08_before = tree_snapshot(ROOT / "books" / "DM08")
        self.manager.status()
        self.assertEqual(graph_before, tree_snapshot(ROOT / "research" / "source-graph"))
        self.assertEqual(dm08_before, tree_snapshot(ROOT / "books" / "DM08"))


if __name__ == "__main__":
    unittest.main()
