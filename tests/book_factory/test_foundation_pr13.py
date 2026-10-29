import unittest
from pathlib import Path

from book_factory.catalogue import CatalogueStore
from book_factory.director import FactoryDirector
from book_factory.util import load_json, sha256_bytes


ROOT = Path(__file__).resolve().parents[2]
BOOK_ROOT = ROOT / "books" / "DM04"
PREVIEW_ROOT = (
    BOOK_ROOT
    / "three-page-acceptance"
    / "page-previews"
    / "page-27d143ae995bf60742b65c5b"
)
REPORT_ROOT = ROOT / "book-factory" / "reports"


class PR13ThreePageAcceptanceTests(unittest.TestCase):
    def test_01_sequence_is_locked_pages_one_through_three(self):
        coverage = load_json(REPORT_ROOT / "pr13-three-page-sequence-asset-coverage.json")
        self.assertEqual(coverage["selection"]["page_numbers"], [1, 2, 3])
        self.assertEqual(
            [page["page_id"] for page in coverage["selection"]["locked_pages"]],
            [
                "page-27d143ae995bf60742b65c5b",
                "page-fe9965a25ead5b61a664263b",
                "page-c599d254a2e3ff2c4d1ba8e0",
            ],
        )
        self.assertEqual(coverage["selection"]["source_order"], ["dm-event-008", "dm-event-008", "dm-event-009"])

    def test_02_every_existing_source_illustration_is_hash_bound_and_audited(self):
        coverage = load_json(REPORT_ROOT / "pr13-three-page-sequence-asset-coverage.json")
        audits = coverage["image_audit"]
        self.assertEqual(len(audits), 15)
        self.assertEqual(len({item["path"] for item in audits}), 15)
        allowed = {
            "REUSE_AS_IS",
            "REUSE_WITH_LAYOUT_REPAIR",
            "LOCAL_IMAGE_EDIT_REQUIRED",
            "NEW_IMAGE_REQUIRED",
            "REJECT_FOR_THIS_SEQUENCE",
        }
        for item in audits:
            self.assertIn(item["classification"], allowed)
            self.assertEqual(sha256_bytes((ROOT / item["path"]).read_bytes()), item["sha256"])

    def test_03_page_one_repair_preserves_text_images_and_font_size(self):
        original = load_json(
            BOOK_ROOT
            / "autonomous-pilot"
            / "page-previews"
            / "page-27d143ae995bf60742b65c5b"
            / "v0001.spec.json"
        )
        repaired = load_json(PREVIEW_ROOT / "v0001.spec.json")
        script = load_json(BOOK_ROOT / "page-scripts" / "page-0001.v0003.json")
        expected_dialogue = next(item["text"] for item in script["lettering"] if item["id"] == "p01-dialogue")
        self.assertEqual(repaired["lettering"][1]["text"], expected_dialogue)
        self.assertEqual(repaired["lettering"][1]["font"], original["lettering"][1]["font"])
        self.assertEqual(repaired["lettering"][1]["font"]["size"], 25)
        self.assertGreaterEqual(repaired["lettering"][1]["font"]["minimum_size"], 22)
        self.assertLess(repaired["lettering"][1]["box"]["height"], original["lettering"][1]["box"]["height"])
        self.assertEqual(
            [panel["asset"]["sha256"] for panel in repaired["panels"]],
            [panel["asset"]["sha256"] for panel in original["panels"]],
        )
        self.assertFalse(repaired["mechanical_repair"]["image_pixels_modified"])
        self.assertFalse(repaired["mechanical_repair"]["image_operation_consumed"])

    def test_04_corrected_page_and_independent_review_pass_private_only(self):
        output = PREVIEW_ROOT / "v0001"
        png = output / "0001-page-27d143ae995bf60742b65c5b.png"
        validation = load_json(output / "0001-page-27d143ae995bf60742b65c5b.validation.json")
        review = load_json(REPORT_ROOT / "pr13-independent-page-review.json")
        self.assertEqual(validation["result"], "PASS")
        self.assertEqual(review["overall_verdict"], "PASS")
        self.assertEqual(len(review["assessments"]), 12)
        self.assertTrue(all(item["result"] == "PASS" for item in review["assessments"]))
        self.assertTrue(review["private_pdf_proof_eligible"])
        self.assertFalse(review["publication_eligible"])
        self.assertFalse(review["source_images_promoted"])
        self.assertEqual(sha256_bytes(png.read_bytes()), review["composed_png"]["sha256"])

    def test_05_missing_art_plan_is_exactly_five_distinct_panels(self):
        plan = load_json(REPORT_ROOT / "pr13-minimal-missing-illustration-specification.json")
        self.assertEqual(plan["minimum_additional_image_operations"], 5)
        self.assertEqual(
            [item["panel_id"] for item in plan["missing_panels"]],
            ["p02-panel-01", "p02-panel-02", "p03-panel-01", "p03-panel-02", "p03-panel-03"],
        )
        self.assertTrue(all(item["new_generation_unavoidable"] for item in plan["missing_panels"]))
        self.assertTrue(all(not item["local_edit_possible"] for item in plan["missing_panels"]))
        self.assertEqual(plan["pr13_execution"]["image_operations"], 0)

    def test_06_full_book_counts_distinguish_facts_from_estimates(self):
        readiness = load_json(REPORT_ROOT / "pr13-dm04-full-book-readiness.json")
        facts = readiness["observed_facts"]
        estimates = readiness["conservative_estimates"]
        self.assertEqual(facts["locked_storyboard_pages"], 32)
        self.assertEqual(facts["locked_storyboard_panel_slots"], 67)
        self.assertEqual(facts["pages_with_usable_private_preview_art"], 1)
        self.assertEqual(facts["pages_with_no_existing_source_art"], 25)
        self.assertEqual(facts["pages_with_existing_art_but_blocking_source_or_iconography_findings"], 6)
        self.assertEqual(estimates["new_panel_images_likely_required"], 61)
        self.assertEqual(estimates["panel_assets_likely_recoverable_by_local_image_edit"], 4)
        self.assertEqual(estimates["minimum_remaining_image_operations_if_each_locked_panel_gets_one_distinct_asset"], 65)

    def test_07_pdf_is_one_reviewed_native_page_and_never_promoted(self):
        pdf_path = ROOT / "output" / "pdf" / "dm04-pr13-one-page-private-diagnostic-proof.pdf"
        inspection = load_json(pdf_path.with_suffix(".inspection.json"))
        self.assertEqual(inspection["result"], "PASS")
        self.assertEqual(inspection["page_count"], 1)
        self.assertEqual(inspection["page_order"], ["page-27d143ae995bf60742b65c5b"])
        self.assertEqual(sha256_bytes(pdf_path.read_bytes()), inspection["pdf_sha256"])
        result = FactoryDirector(ROOT).inspect_pdf(
            pdf_path,
            BOOK_ROOT / "three-page-acceptance" / "pdf-proof" / "pr13-private-diagnostic-proof.manifest.json",
            private_preview=True,
        )
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["publication_state_transition"], "PROHIBITED_PRIVATE_PREVIEW")

    def test_08_campaign_counters_catalogue_and_dm08_exclusion_are_preserved(self):
        status = load_json(BOOK_ROOT / "autonomous-pilot-status.json")
        self.assertEqual(status["image_operations_executed"], 5)
        self.assertEqual(status["remaining_image_operations"], 0)
        self.assertFalse(status["pr6_counter_reset"])
        self.assertFalse(status["pr11_counter_reset"])
        catalogue = CatalogueStore(ROOT / "books" / "catalogue.json")
        self.assertEqual(len(catalogue.list_books()), 78)
        self.assertEqual(catalogue.get("DM08")["factory"]["edition_status"], "EXISTING_EDITION")
        queue = {item["book_id"]: item for item in FactoryDirector(ROOT).factory_queue()["entries"]}
        self.assertEqual(queue["DM08"]["queue_status"], "EXCLUDED")
        self.assertFalse(queue["DM08"]["private_production_eligible"])


if __name__ == "__main__":
    unittest.main()
