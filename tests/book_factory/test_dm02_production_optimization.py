import unittest
from pathlib import Path

from book_factory.director import FactoryDirector
from book_factory.preproduction import validate_storyboard
from book_factory.util import content_hash, load_json, sha256_bytes
from book_factory.versioning import (
    CharacterBibleVersionStore,
    LocationBibleVersionStore,
    ManuscriptVersionStore,
    ProofSpecVersionStore,
    StoryboardVersionStore,
)


ROOT = Path(__file__).resolve().parents[2]
BOOKS = ROOT / "books"
BOOK_ID = "DM02"
V1_CAMPAIGN_HASH = "5afc3beed39e3a79a40e768f172c188691ef6cbf5d5938eca229c49aabb0fcf4"
V2_CAMPAIGN_HASH = "0465f0111d3fac1729014bb95ac5247e417aaf3429672ebc5f69e79f18fdac1e"
V2_SUBJECT_HASH = "022e685794c7a807a2850c0522791db72944f52e785355b0f396d7ea4e49ee69"


class DM02ProductionOptimizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.storyboards = StoryboardVersionStore(BOOKS).versions(BOOK_ID)
        cls.v1_record, cls.v2_record = cls.storyboards
        cls.v1 = cls.v1_record["payload"]
        cls.v2 = cls.v2_record["payload"]
        cls.campaign = load_json(BOOKS / BOOK_ID / "image-campaigns" / (V2_CAMPAIGN_HASH + ".request.json"))

    def test_01_storyboard_v1_is_preserved_and_v2_is_parent_linked(self):
        self.assertEqual(self.v1_record["content_hash"], "21b197e30af545ba39f2e1004b5132ccfecee5cfef662bb6eec913675cbf33f6")
        self.assertEqual(self.v2_record["content_hash"], "b3bc6d96458730500a3a3361a5382796cdd3f882c9a51eb59f25648c3ea94f28")
        self.assertEqual(self.v2_record["parent_hash"], self.v1_record["content_hash"])
        self.assertEqual(self.v2["parent_storyboard_record_hash"], self.v1_record["content_hash"])
        self.assertEqual(content_hash(self.v2), "e50ba7af25ce1c1091e83e52ddabab3568982705c0d38b87ef07dac0604971c2")

    def test_02_manuscript_lettering_events_and_moments_are_unchanged(self):
        manuscripts = ManuscriptVersionStore(BOOKS).versions(BOOK_ID)
        self.assertEqual(len(manuscripts), 2)
        self.assertEqual(manuscripts[-1]["content_hash"], "ca54ad2d167ceb36bbcd10b33a9d5350aba6fae98c19693cef07bf41709dd762")
        self.assertEqual(
            [page["lettering"] for page in self.v2["pages"]],
            [page["lettering"] for page in self.v1["pages"]],
        )
        self.assertEqual(
            {event for page in self.v2["pages"] for event in page["event_ids"]},
            {"dm-event-004", "dm-event-005", "dm-event-006", "dm-event-007"},
        )
        self.assertEqual(
            {moment for page in self.v2["pages"] for moment in page["moment_ids"]},
            {item["id"] for item in self.v2["required_moments"]},
        )

    def test_03_v2_keeps_reader_rhythm_and_reduces_raster_masters(self):
        panels = [panel for page in self.v2["pages"] for panel in page["panels"]]
        self.assertEqual(len(self.v2["pages"]), 24)
        self.assertEqual(len(panels), 44)
        self.assertEqual(sum(panel["production_plan"]["requires_new_raster_generation"] for panel in panels), 35)
        self.assertEqual(sum(panel["production_plan"]["classification"] == "REFRAME_EXISTING_ART" for panel in panels), 7)
        self.assertEqual(sum(panel["production_plan"]["asset_source"] == "DETERMINISTIC_TYPOGRAPHY_AND_SERIES_ORNAMENT_RULES" for panel in panels), 2)
        self.assertEqual(
            [page["page_number"] for page in self.v2["pages"] if page["layout"]["type"] == "FULL_PAGE"],
            [3, 4, 6, 9, 11, 15, 21],
        )
        self.assertTrue(all(panel["lineage"]["original_panel_ids"] == [panel["id"]] for panel in panels))

    def test_04_v2_and_proof_specs_pass_exact_validation(self):
        manuscript = ManuscriptVersionStore(BOOKS).versions(BOOK_ID)[-1]
        character = CharacterBibleVersionStore(BOOKS).versions(BOOK_ID)[-1]["payload"]
        location = LocationBibleVersionStore(BOOKS).versions(BOOK_ID)[-1]["payload"]
        gate = validate_storyboard(
            self.v2,
            {"dm-event-004", "dm-event-005", "dm-event-006", "dm-event-007"},
            manuscript["payload"],
            character,
            location,
            expected_manuscript_hash=manuscript["content_hash"],
            required_moment_ids={item["id"] for item in self.v2["required_moments"]},
        )
        self.assertEqual(gate["result"], "PASS")
        proof = ProofSpecVersionStore(BOOKS).versions(BOOK_ID)[-1]
        self.assertEqual(proof["version"], 2)
        self.assertEqual(proof["payload"]["storyboard_hash"], content_hash(self.v2))
        self.assertIn("source-neutral", next(item for item in proof["payload"]["specs"] if item["id"] == "dm02-proof-full-page")["composition"])

    def test_05_both_independent_exact_v2_reviews_pass(self):
        source = load_json(ROOT / "book-factory" / "reports" / "dm02-storyboard-v2-source-storytelling-review.json")
        visual = load_json(ROOT / "book-factory" / "reports" / "dm02-storyboard-v2-visual-production-review.json")
        self.assertEqual(source["result"], "PASS")
        self.assertEqual(visual["result"], "PASS")
        self.assertEqual(source["exact_input_bindings"]["storyboard_v2"]["record_hash"], self.v2_record["content_hash"])
        self.assertEqual(visual["input_bindings"]["storyboard_v2"]["record_content_hash"], self.v2_record["content_hash"])
        self.assertNotEqual(source["reviewer"]["id"], visual["reviewer"]["agent_id"])

    def test_06_new_campaign_is_exact_blocked_and_review_bound(self):
        self.assertEqual(self.campaign["campaign_hash"], V2_CAMPAIGN_HASH)
        self.assertEqual(self.campaign["authorization_subject_hash"], V2_SUBJECT_HASH)
        self.assertEqual(self.campaign["status"], "AWAITING_CAMPAIGN_AUTHORIZATION")
        self.assertFalse(self.campaign["approval_record_created"])
        self.assertEqual(self.campaign["image_operations_executed"], 0)
        self.assertEqual(self.campaign["counts"], {
            "storyboard_pages": 24,
            "storyboard_panels": 44,
            "illustrated_panel_slots": 42,
            "panels_needing_new_art": 35,
            "existing_usable_assets": 0,
            "image_edit_opportunities": 0,
            "shared_master_reframe_targets": 7,
            "deterministic_layout_only_panels": 2,
            "initial_generation_operations": 35,
            "maximum_retry_operations": 9,
            "maximum_total_operations": 44,
        })
        self.assertEqual(len(self.campaign["units"]), 35)
        self.assertEqual([item["operation_order"] for item in self.campaign["units"]], list(range(1, 36)))
        self.assertEqual(self.campaign["generation_plan"]["suggested_batch_size"], 4)
        roles = {item["role"] for item in self.campaign["locked_inputs"]}
        self.assertIn("STORYBOARD_V2_SOURCE_STORYTELLING_REVIEW", roles)
        self.assertIn("STORYBOARD_V2_VISUAL_PRODUCTION_REVIEW", roles)

    def test_07_old_campaign_is_immutable_and_no_media_exists(self):
        old_path = BOOKS / BOOK_ID / "image-campaigns" / (V1_CAMPAIGN_HASH + ".request.json")
        self.assertEqual(sha256_bytes(old_path.read_bytes()), "8e3a3d5ee5437f0d7e9f44a3b228ac6674f2250216a7e335f3a0173a30247c7d")
        self.assertFalse((BOOKS / BOOK_ID / "generated-images").exists())
        self.assertFalse((BOOKS / BOOK_ID / "composed-pages").exists())
        self.assertFalse((BOOKS / BOOK_ID / "pdfs").exists())

    def test_08_usage_is_observed_without_false_cost_certainty(self):
        usage = self.campaign["allowance_observation"]
        self.assertEqual(usage["codex_used_percent"], 26)
        self.assertEqual(usage["codex_remaining_percent"], 74)
        self.assertFalse(usage["has_purchased_credits"])
        self.assertEqual(usage["purchased_credit_balance"], "0")
        boundary = self.campaign["cost_and_credit_boundary"]
        self.assertFalse(boundary["zero_incremental_usd_enforceable_by_repository"])
        self.assertEqual(boundary["built_in_image_operation_allowance_bucket"], "NOT_EXPOSED_BY_HOST_TOOL_OR_READ_ONLY_USAGE_CONTROL")

    def test_09_campaign_freeze_is_idempotent(self):
        result = FactoryDirector(ROOT).prepare_complete_book_image_campaign(
            BOOK_ID,
            BOOKS / BOOK_ID / "usage-observations" / "2026-10-22T073059Z.json",
        )
        self.assertEqual(result["campaign_hash"], V2_CAMPAIGN_HASH)
        self.assertEqual(result["authorization_subject_hash"], V2_SUBJECT_HASH)
        self.assertFalse(result["approval_record_created"])


if __name__ == "__main__":
    unittest.main()
