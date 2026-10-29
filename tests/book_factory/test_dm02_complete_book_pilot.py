import unittest
from pathlib import Path

from book_factory.director import FactoryDirector
from book_factory.editorial import PR5_REVIEW_PERSPECTIVES
from book_factory.errors import ContractError
from book_factory.state import page_id
from book_factory.util import load_json
from book_factory.versioning import EditorialReviewStore, ManuscriptVersionStore, StoryboardVersionStore


ROOT = Path(__file__).resolve().parents[2]
BOOKS = ROOT / "books"
BOOK_ID = "DM02"
EVENT_IDS = {"dm-event-004", "dm-event-005", "dm-event-006", "dm-event-007"}
MOMENT_IDS = {
    "medhas_opens_cosmic_tale",
    "vishnu_sleeps_on_shesha",
    "madhu_kaitabha_threaten_brahma",
    "brahma_invokes_goddess",
    "yoganidra_leaves_vishnu",
    "vishnu_awakens",
    "long_combat_shown_nonliterally",
    "demons_offer_unusual_boon",
    "vishnu_names_their_death",
    "unflooded_condition_and_defeat",
    "resolved_return_to_frame",
    "source_and_adaptation_notes",
}
CAMPAIGN_HASH = "5afc3beed39e3a79a40e768f172c188691ef6cbf5d5938eca229c49aabb0fcf4"
SUBJECT_HASH = "e9c4635fdafaca4b1a4db2c9ae9bc09b494e5a2142ab67340889a0e3f32994fc"


class DM02CompleteBookPilotTests(unittest.TestCase):
    def setUp(self):
        self.manuscript_record = ManuscriptVersionStore(BOOKS).versions(BOOK_ID)[-1]
        self.manuscript = self.manuscript_record["payload"]
        self.storyboard = StoryboardVersionStore(BOOKS).versions(BOOK_ID)[-1]["payload"]
        self.campaign = load_json(BOOKS / BOOK_ID / "image-campaigns" / (CAMPAIGN_HASH + ".request.json"))

    def test_01_complete_revised_manuscript_and_event_coverage(self):
        self.assertEqual(self.manuscript_record["version"], 2)
        self.assertEqual(self.manuscript_record["content_hash"], "ca54ad2d167ceb36bbcd10b33a9d5350aba6fae98c19693cef07bf41709dd762")
        self.assertEqual(len(self.manuscript["chapters"]), 8)
        self.assertEqual(sum(len(chapter["text"].split()) for chapter in self.manuscript["chapters"]), 1202)
        self.assertEqual({item["event_id"] for item in self.manuscript["event_coverage"]}, EVENT_IDS)

    def test_02_latest_manuscript_has_two_independent_pass_reviews(self):
        reviews = [
            item["payload"] for item in EditorialReviewStore(BOOKS).versions(BOOK_ID)
            if item["payload"].get("reviewed_manuscript_hash") == self.manuscript_record["content_hash"]
        ]
        self.assertEqual({item["review_perspective"] for item in reviews}, set(PR5_REVIEW_PERSPECTIVES))
        self.assertTrue(all(item["result"] == "PASS" for item in reviews))
        self.assertEqual(len({item["reviewer"]["id"] for item in reviews}), 2)
        self.assertTrue(all(item["reviewer"]["id"] != self.manuscript["creator"]["id"] for item in reviews))

    def test_03_storyboard_is_complete_and_complexity_derived(self):
        self.assertEqual(len(self.storyboard["pages"]), 24)
        self.assertEqual(sum(len(page["panels"]) for page in self.storyboard["pages"]), 44)
        self.assertEqual(sum(len(page["lettering"]) for page in self.storyboard["pages"]), 44)
        for number, page in enumerate(self.storyboard["pages"], 1):
            self.assertEqual(page["page_number"], number)
            self.assertEqual(page["page_id"], page_id(BOOK_ID, number))
            self.assertEqual(page["reading_order"], [panel["id"] for panel in page["panels"]])
            self.assertTrue(all(not panel["image_instructions"]["render"] for panel in page["panels"]))
        self.assertEqual([page["page_number"] for page in self.storyboard["pages"] if page["layout"]["type"] == "FULL_PAGE"], [3, 4, 6, 9, 11, 15, 21])
        self.assertEqual(self.storyboard["pages"][-2]["layout"]["type"], "BACK_MATTER")
        self.assertEqual(self.storyboard["pages"][-1]["layout"]["type"], "BACK_MATTER")

    def test_04_all_locked_moments_are_declared_and_placed_once(self):
        self.assertEqual({item["id"] for item in self.storyboard["required_moments"]}, MOMENT_IDS)
        placements = [moment for page in self.storyboard["pages"] for moment in page["moment_ids"]]
        self.assertEqual(set(placements), MOMENT_IDS)
        self.assertEqual(len(placements), len(MOMENT_IDS))

    def test_05_campaign_is_exact_non_executing_and_fail_closed(self):
        self.assertEqual(self.campaign["authorization_subject_hash"], SUBJECT_HASH)
        self.assertEqual(self.campaign["status"], "AWAITING_CAMPAIGN_AUTHORIZATION")
        self.assertFalse(self.campaign["approval_record_created"])
        self.assertEqual(self.campaign["image_operations_executed"], 0)
        self.assertEqual(self.campaign["counts"], {
            "storyboard_pages": 24,
            "storyboard_panels": 44,
            "panels_needing_new_art": 44,
            "existing_usable_assets": 0,
            "image_edit_opportunities": 0,
            "initial_generation_operations": 44,
            "maximum_retry_operations": 44,
            "maximum_total_operations": 88,
        })
        subject = self.campaign["authorization_subject"]
        self.assertFalse(subject["api_key_authorized"])
        self.assertFalse(subject["external_provider_authorized"])
        self.assertFalse(subject["purchased_credits_authorized"])
        self.assertFalse(subject["automatic_credit_purchase_authorized"])
        self.assertFalse(subject["workspace_overage_authorized"])
        self.assertEqual(subject["maximum_paid_spend_minor_units"], 0)
        self.assertFalse(subject["private_illustration_clearance_present"])
        self.assertTrue(subject["private_illustration_clearance_required_before_execution"])
        self.assertEqual({item["role"] for item in self.campaign["locked_inputs"]}, {
            "MANUSCRIPT", "STORYBOARD", "CHARACTER_BIBLE", "LOCATION_BIBLE", "TYPOGRAPHY",
            "PROOF_SPECS", "PR7_VISUAL_GOLD_STANDARD", "CODEX_USAGE_OBSERVATION",
            "SOURCE_READINESS_DOSSIER", "SOURCE_CLEARANCE", "STORY_PACKET",
        })

    def test_06_usage_is_observed_but_not_monetarily_guaranteed(self):
        usage = self.campaign["allowance_observation"]
        self.assertTrue(usage["ordinary_usage_allowed"])
        self.assertEqual(usage["codex_used_percent"], 24)
        self.assertEqual(usage["codex_remaining_percent"], 76)
        self.assertFalse(usage["has_purchased_credits"])
        self.assertEqual(usage["purchased_credit_balance"], "0")
        self.assertFalse(self.campaign["cost_and_credit_boundary"]["zero_incremental_usd_enforceable_by_repository"])

    def test_07_no_images_pages_or_pdf_were_produced(self):
        self.assertFalse((BOOKS / BOOK_ID / "generated-images").exists())
        self.assertFalse((BOOKS / BOOK_ID / "composed-pages").exists())
        self.assertFalse((BOOKS / BOOK_ID / "pdfs").exists())
        self.assertTrue(all(item["operation"] == "generate" for item in self.campaign["units"]))

    def test_08_complete_book_planner_is_dm02_only(self):
        with self.assertRaises(ContractError):
            FactoryDirector(ROOT).prepare_complete_book_image_campaign(
                "DM04", BOOKS / BOOK_ID / "usage-observations" / "2026-10-22T052232Z.json"
            )


if __name__ == "__main__":
    unittest.main()
