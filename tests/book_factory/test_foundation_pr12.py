import unittest
from pathlib import Path

from book_factory.approvals import ApprovalStore
from book_factory.autonomous_pilot import (
    BOOK_ID,
    CAMPAIGN_ID,
    MAXIMUM_OPERATIONS,
    UNITS,
    AutonomousMultiPagePilot,
)
from book_factory.catalogue import CatalogueStore
from book_factory.director import FactoryDirector
from book_factory.errors import ContractError
from book_factory.illustration_production import inspect_png
from book_factory.production_integration import REVIEW_DIMENSIONS
from book_factory.util import load_json, sha256_bytes, tree_snapshot


ROOT = Path(__file__).resolve().parents[2]
BOOK_ROOT = ROOT / "books" / BOOK_ID

IMAGE_HASHES = {
    "page-27d143ae995bf60742b65c5b--p01-panel-02": "3fc146fd6d5afc5a512537ace1e23b132c769b6fbc5bcff99f2fbb7d39f93ea9",
    "page-23e0e9cd9d4013ed03ae7e8c--p13-panel-01": "c0a0d15ea531ba00bee1c1c3ccac1bb795dc84f59e0a25d96dd08eca1b6a09b4",
    "page-23e0e9cd9d4013ed03ae7e8c--p13-panel-02": "e303a5c2cd40c5c9b59ed7e4fd4b3a77c11c9f838ab43b095311d1677746105d",
    "page-5aca23381e148b472373cd8c--p14-panel-01": "6f4740c453c6d6429c9bcc1f32eaee0bb3023d6892d3e58a10281f947927ca45",
    "page-54d61ef5bfcb1159088ac489--p23-panel-01": "6d41a3604423dfab3e1f31e6fc00c034fa40325173fbfcf26e70826548891e07",
}

REFERENCE_HASHES = {
    "kgs-satya-p01": "15c2cfaf37a379c8042105051ac432e3aba5ccc0594eef43dc95d157cee53a1b",
    "kgs-dm08-p09": "26f5a3d7fdc9c9432f0a793c6b50711a2bb4b1157cde79a7534c542a6c9bfa2d",
    "kgs-dm08-p21": "332b208d14df3d94139a3ab598e7e7e327e49bc9d4bbf5f41ddf20d8260291af",
    "kgs-dm08-p12": "d46f264508cf0283e56f14d1a02b6d66b37a49b8e2e66c7b3f31f16764fadfe4",
    "kgs-dm08-p28": "7c57ff55122e1054aa36cc9c4a122c9c9245a71152068da3b0b6b2dd02f9fdb5",
}


class PR12AutonomousMultiPagePilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manager = AutonomousMultiPagePilot(ROOT)
        cls.status = cls.manager.status()["run"]
        records = sorted(
            (load_json(path) for path in (BOOK_ROOT / "production-slices").glob("v*.json")),
            key=lambda record: record["version"],
        )
        cls.plan_record = next(
            record for record in reversed(records)
            if record["payload"].get("campaign_id") == CAMPAIGN_ID
        )
        cls.plan = cls.plan_record["payload"]

    def _record(self, kind, unit_id):
        return load_json(BOOK_ROOT / kind / unit_id / "v0001.json")

    def test_01_campaign_is_exactly_five_one_shot_units(self):
        self.assertEqual(self.plan["milestone"], "PR12")
        self.assertEqual(self.plan["campaign_id"], CAMPAIGN_ID)
        self.assertEqual(len(self.plan["units"]), MAXIMUM_OPERATIONS)
        self.assertEqual([item["unit_id"] for item in self.plan["units"]], [item["unit_id"] for item in UNITS])
        self.assertTrue(all(item["operation_ceiling"] == 1 for item in self.plan["units"]))
        self.assertEqual([item["operation"] for item in self.plan["units"]], ["edit", "generate", "generate", "generate", "generate"])

    def test_02_exact_non_inheritable_human_approval_is_bound(self):
        approval = next(
            item for item in ApprovalStore(BOOK_ROOT / "approvals").list()
            if item["id"] == self.status["approval_id"]
        )
        self.assertEqual(approval["subject_hash"], self.plan["authorization_subject_hash"])
        self.assertFalse(approval["inheritance_allowed"])
        self.assertEqual(approval["approver"]["id"], "human-user-current-session-pr12")
        self.assertNotIn("signature", approval["approver"])

    def test_03_locked_story_events_and_exact_lettering_are_preserved(self):
        for unit in self.plan["units"]:
            script = load_json(ROOT / unit["page_script"]["path"])
            panel = next(item for item in script["panels"] if item["id"] == unit["panel_id"])
            self.assertEqual(unit["event_ids"], script["event_ids"])
            self.assertEqual(unit["locked_action"], panel["visual_description"])
            self.assertEqual(unit["lettering"], script["lettering"])

    def test_04_actual_pngs_are_hash_bound_and_readable(self):
        self.assertEqual(set(IMAGE_HASHES), {item["unit_id"] for item in self.plan["units"]})
        for unit_id, expected_hash in IMAGE_HASHES.items():
            receipt = self._record("autonomous-pilot-image-receipts", unit_id)["payload"]
            image = ROOT / receipt["image"]["path"]
            self.assertEqual(sha256_bytes(image.read_bytes()), expected_hash)
            self.assertEqual(receipt["image"]["sha256"], expected_hash)
            self.assertTrue(inspect_png(image)["readable"])

    def test_05_actual_reference_inputs_and_roles_are_preserved(self):
        for unit in self.plan["units"]:
            available = [item for item in unit["references"] if item["available"]]
            self.assertEqual([item["role"] for item in available], ["A_SERIES_VISUAL_IDENTITY", "B_PAGE_PANEL_COMPOSITION"])
            self.assertEqual(
                [item["role"] for item in unit["references"] if not item["available"]],
                ["C_APPROVED_CHARACTER_REFERENCE", "D_APPROVED_SETTING_REFERENCE"],
            )
            for reference in available:
                self.assertEqual(reference["sha256"], REFERENCE_HASHES[reference["reference_id"]])
                self.assertEqual(sha256_bytes((ROOT / reference["path"]).read_bytes()), reference["sha256"])

    def test_06_provider_receipts_report_only_the_built_in_allowance_first_path(self):
        for sequence, unit in enumerate(self.plan["units"], 1):
            provider = load_json(
                BOOK_ROOT / "autonomous-pilot" / "provider-receipts" / unit["unit_id"] / "v0001.json"
            )
            self.assertEqual(provider["operation_sequence"], sequence)
            self.assertEqual(provider["provider_id"], "codex-built-in-image-gen")
            self.assertEqual(provider["provider_interface"], "image_gen.imagegen")
            self.assertEqual(provider["included_allowance_policy"], "CURRENT_INCLUDED_ALLOWANCE_FIRST")
            self.assertFalse(provider["api_key_supplied"])
            self.assertFalse(provider["paid_billing_requested"])
            self.assertFalse(provider["external_provider_authorization_requested"])
            self.assertFalse(provider["automatic_credit_purchase_requested"])
            self.assertFalse(provider["retry"])
            self.assertEqual(provider["actual_incremental_usd"], "UNKNOWN_NOT_EXPOSED")

    def test_07_operation_ceiling_is_exhausted_without_retry(self):
        self.assertEqual(self.status["image_operations_executed"], MAXIMUM_OPERATIONS)
        self.assertEqual(self.status["remaining_image_operations"], 0)
        with self.assertRaises(ContractError):
            self.manager.prepare_generation(self.plan["units"][0]["unit_id"])

    def test_08_all_images_received_independent_actual_pixel_review(self):
        self.assertEqual(self.status["independent_reviews_completed"], MAXIMUM_OPERATIONS)
        for unit in self.plan["units"]:
            review = self._record("autonomous-pilot-visual-reviews", unit["unit_id"])["payload"]
            self.assertEqual(review["image_sha256"], IMAGE_HASHES[unit["unit_id"]])
            self.assertEqual(review["reviewer"]["id"], "/root/pr12_visual_reviewer")
            self.assertTrue(review["reviewer"]["inspected_actual_pixels"])
            self.assertFalse(review["reviewer"]["produced_image"])
            self.assertEqual([item["dimension"] for item in review["assessments"]], list(REVIEW_DIMENSIONS))
            self.assertEqual(review["result"], "FIX")
            self.assertFalse(review["publication_eligible"])

    def test_09_failed_images_have_local_corrections_but_no_retry_authority(self):
        for unit in self.plan["units"]:
            correction = self._record("autonomous-pilot-correction-requests", unit["unit_id"])["payload"]
            self.assertEqual(correction["failed_image_sha256"], IMAGE_HASHES[unit["unit_id"]])
            self.assertFalse(correction["generation_retry_authorized"])
            self.assertFalse(correction["pr6_counter_reset"])
            self.assertFalse(correction["pr11_counter_reset"])
            self.assertTrue(correction["preserve_other_units"])

    def test_10_cost_is_not_invented_and_no_separate_provider_call_is_recorded(self):
        self.assertEqual(self.status["actual_incremental_usd"], "UNKNOWN_NOT_EXPOSED")
        self.assertEqual(self.status["separately_billed_provider_calls"], 0)
        self.assertEqual(self.status["purchased_credit_consumption"], "NOT_REQUESTED_OR_REPORTED")

    def test_11_pr6_and_pr11_counters_are_unchanged(self):
        pr6 = load_json(BOOK_ROOT / "production-status.json")
        pr11 = load_json(BOOK_ROOT / "production-integration-status.json")
        preservation = self.plan["preservation"]
        self.assertEqual(pr6["real_images_generated_total"], preservation["pr6_real_images_generated_total_before"])
        self.assertEqual(pr6["exact_result"], preservation["pr6_exact_result_before"])
        self.assertEqual(pr11["actual_image_operations"], preservation["pr11_operations_before"])
        self.assertFalse(self.status["pr6_counter_reset"])
        self.assertFalse(self.status["pr11_counter_reset"])

    def test_12_prepare_is_idempotent_across_shared_campaign_stores(self):
        before_slices = len(list((BOOK_ROOT / "production-slices").glob("v*.json")))
        before_requests = len(list((BOOK_ROOT / "production-campaign-requests").glob("v*.json")))
        graph_before = tree_snapshot(ROOT / "research" / "source-graph")
        dm08_before = tree_snapshot(ROOT / "books" / "DM08")
        repeated = self.manager.prepare()
        self.assertEqual(repeated["run"]["image_operations_executed"], MAXIMUM_OPERATIONS)
        self.assertEqual(before_slices, len(list((BOOK_ROOT / "production-slices").glob("v*.json"))))
        self.assertEqual(before_requests, len(list((BOOK_ROOT / "production-campaign-requests").glob("v*.json"))))
        self.assertEqual(graph_before, tree_snapshot(ROOT / "research" / "source-graph"))
        self.assertEqual(dm08_before, tree_snapshot(ROOT / "books" / "DM08"))

    def test_13_catalogue_and_existing_edition_exclusion_are_preserved(self):
        catalogue = CatalogueStore(ROOT / "books" / "catalogue.json")
        self.assertEqual(len(catalogue.list_books()), 78)
        dm08 = catalogue.get("DM08")
        self.assertEqual(dm08["factory"]["edition_status"], "EXISTING_EDITION")
        queue = {item["book_id"]: item for item in FactoryDirector(ROOT).factory_queue()["entries"]}
        self.assertEqual(queue["DM08"]["queue_status"], "EXCLUDED")
        self.assertFalse(queue["DM08"]["private_production_eligible"])

    def test_14_campaign_stops_with_publication_blocked(self):
        self.assertEqual(self.status["status"], "REVIEWED_WITH_BLOCKERS_CAMPAIGN_COMPLETE_NO_RETRY")
        self.assertFalse(self.status["publication_eligible"])
        self.assertFalse(self.plan["publication_eligible"])

    def test_15_one_mechanically_repaired_page_passes_private_preview_only(self):
        preview_root = (
            BOOK_ROOT / "autonomous-pilot" / "page-previews" /
            "page-27d143ae995bf60742b65c5b" / "v0001"
        )
        review = load_json(preview_root / "0001-page-27d143ae995bf60742b65c5b.visual-review.json")
        self.assertEqual(review["overall_verdict"], "PASS")
        self.assertTrue(review["private_pdf_proof_eligible"])
        self.assertFalse(review["publication_eligible"])
        self.assertFalse(review["source_images_promoted"])
        self.assertEqual(
            sha256_bytes((ROOT / review["composed_png"]["path"]).read_bytes()),
            review["composed_png"]["sha256"],
        )
        validation = load_json(preview_root / "0001-page-27d143ae995bf60742b65c5b.validation.json")
        self.assertEqual(validation["result"], "PASS")

    def test_16_private_pdf_is_one_reviewed_native_page_and_never_promoted(self):
        pdf_path = ROOT / "output" / "pdf" / "dm04-pr12-private-diagnostic-proof.pdf"
        inspection_path = pdf_path.with_suffix(".inspection.json")
        inspection = load_json(inspection_path)
        self.assertEqual(inspection["result"], "PASS")
        self.assertEqual(inspection["page_count"], 1)
        self.assertEqual(inspection["page_order"], ["page-27d143ae995bf60742b65c5b"])
        self.assertEqual(
            (inspection["pages"][0]["width"], inspection["pages"][0]["height"]),
            (1086.0, 1448.0),
        )
        self.assertEqual(sha256_bytes(pdf_path.read_bytes()), inspection["pdf_sha256"])
        result = FactoryDirector(ROOT).inspect_pdf(
            pdf_path,
            BOOK_ROOT / "autonomous-pilot" / "pdf-proof" / "pr12-private-diagnostic-proof.manifest.json",
            private_preview=True,
        )
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["publication_state_transition"], "PROHIBITED_PRIVATE_PREVIEW")

    def test_17_reports_do_not_claim_zero_cost_or_larger_run_readiness(self):
        usage = load_json(ROOT / "book-factory" / "reports" / "pr12-campaign-usage-and-cost.json")
        autonomy = load_json(ROOT / "book-factory" / "reports" / "pr12-autonomous-production-assessment.json")
        execution = load_json(ROOT / "book-factory" / "reports" / "pr12-autonomous-multi-page-pilot.json")
        self.assertEqual(usage["interpretation"]["actual_incremental_usd"], "UNKNOWN_NOT_EXPOSED")
        self.assertFalse(usage["interpretation"]["positive_zero_usd_verification"])
        self.assertFalse(autonomy["larger_private_run_readiness"]["ready"])
        self.assertEqual(execution["quality"]["publication_ready_pages"], 0)
        self.assertEqual(execution["next_action"], "STOP_PR12_NO_ADDITIONAL_IMAGE_OPERATIONS")


if __name__ == "__main__":
    unittest.main()
