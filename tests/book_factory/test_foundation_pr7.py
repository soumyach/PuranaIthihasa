import copy
import unittest
from collections import Counter
from pathlib import Path

from book_factory.contracts import validate_named
from book_factory.director import FactoryDirector
from book_factory.errors import ContractError
from book_factory.illustration_production import ProofExecutionLedger
from book_factory.source_graph import ReadOnlySourceGraph
from book_factory.util import load_json, sha256_bytes, tree_snapshot
from book_factory.versioning import CharacterReferenceVersionStore, ProofRecoveryRequestVersionStore
from book_factory.visual_benchmark import (
    COMPARATIVE_DIMENSIONS,
    GOLD_CATEGORIES,
    PRODUCTION_UNITS,
    REFERENCE_ROLES,
    build_recovery_payload,
    validate_comparison,
    validate_cultural_authenticity,
    validate_gold_standard,
    validate_lettering_and_units,
    validate_pr7,
    validate_recovery_requests,
)


ROOT = Path(__file__).resolve().parents[2]
BOOKS = ROOT / "books"
GRAPH_ROOT = ROOT / "research" / "source-graph"

EXPECTED_REFERENCE_HASHES = {
    "kgs-satya-p01": "15c2cfaf37a379c8042105051ac432e3aba5ccc0594eef43dc95d157cee53a1b",
    "kgs-satya-p02": "a0fa07b60d1b8b128b541300f3fb5e26358863e3153c719e2d0aacb0fd7858dd",
    "kgs-satya-p04": "9b15d37505c7fcbecac144d031af2e52ed09c95d7e5e4f637abb800f2a66da2a",
    "kgs-satya-p06": "5f04b00c646e5c15d42b86cfd05ce36716b0bc6b2bf4c63be3b243118f64d985",
    "kgs-dm08-p09": "26f5a3d7fdc9c9432f0a793c6b50711a2bb4b1157cde79a7534c542a6c9bfa2d",
    "kgs-dm08-p12": "d46f264508cf0283e56f14d1a02b6d66b37a49b8e2e66c7b3f31f16764fadfe4",
    "kgs-dm08-p21": "332b208d14df3d94139a3ab598e7e7e327e49bc9d4bbf5f41ddf20d8260291af",
    "kgs-dm08-p28": "7c57ff55122e1054aa36cc9c4a122c9c9245a71152068da3b0b6b2dd02f9fdb5",
}


class FoundationPR7AcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load_json(
            ROOT / "book-factory" / "references" / "visual-gold-standard" / "manifest.json"
        )
        cls.blueprint = load_json(ROOT / "book-factory" / "config" / "pr7-dm04-recovery-blueprint.json")
        cls.comparison = load_json(BOOKS / "DM04" / "visual-comparisons" / "pr7-comparison.json")

    def test_01_exact_reference_page_hashes_and_pdf_bindings(self):
        pages = {item["reference_id"]: item for item in self.manifest["pages"]}
        self.assertEqual(set(pages), set(EXPECTED_REFERENCE_HASHES))
        for reference_id, expected in EXPECTED_REFERENCE_HASHES.items():
            page = pages[reference_id]
            self.assertEqual(page["extracted_sha256"], expected)
            self.assertEqual(sha256_bytes((ROOT / page["extracted_path"]).read_bytes()), expected)
        self.assertEqual(
            {item["sha256"] for item in self.manifest["source_assets"]},
            {
                "82ae125d099ef2608adad705922567df6b553db40dd39af64b77c5de28dcadd2",
                "3867fccdd8c8755d27ff06c7543d8002cefb7531c1d4f39c743a43bff9c4a29f",
            },
        )

    def test_02_reference_manifest_validity_and_complete_coverage(self):
        result = validate_gold_standard(ROOT, require_source_assets=True)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(len(result["pages"]), 8)
        self.assertEqual(set(self.manifest["coverage"]), GOLD_CATEGORIES)
        self.assertEqual({item["status"] for item in result["source_assets"]}, {"VERIFIED"})
        malformed = copy.deepcopy(self.manifest)
        malformed["pages"].append(copy.deepcopy(malformed["pages"][0]))
        with self.assertRaises(ContractError):
            validate_named(malformed, ROOT / "schemas" / "book-factory", "visual-gold-standard")

    def test_03_style_and_content_reference_roles_are_separate(self):
        for request in self.blueprint["requests"]:
            roles = {item["role"]: item for item in request["reference_package"]}
            self.assertEqual(set(roles), REFERENCE_ROLES)
            for role in ("REFERENCE_A_SERIES_VISUAL_IDENTITY", "REFERENCE_B_PAGE_COMPOSITION"):
                self.assertEqual(roles[role]["content_transfer"], "FORBIDDEN")
                self.assertIsNotNone(roles[role]["path"])
            self.assertIsNone(roles["REFERENCE_C_CHARACTER_IDENTITY"]["path"])

    def test_04_no_unrelated_deity_or_story_transfer(self):
        prohibited = {
            item.lower()
            for request in self.blueprint["requests"]
            for item in request["prohibited_transfers"]
        }
        joined = " ".join(prohibited)
        for identity in ("vishnu", "narada", "raktabija", "seven mothers"):
            self.assertIn(identity, joined)
        for request in self.blueprint["requests"]:
            prompt = request["concise_prompt"].lower()
            self.assertTrue("copy no" in prompt or "never copy" in prompt or "do not copy" in prompt)

    def test_05_stable_character_and_source_bindings(self):
        first = CharacterReferenceVersionStore(BOOKS).versions("DM04")[-1]["payload"]
        second = CharacterReferenceVersionStore(BOOKS).versions("DM04")[-1]["payload"]
        self.assertEqual(first["registry_hash"], second["registry_hash"])
        expected_ids = {item["reference_id"] for item in first["entries"]}
        for request in self.blueprint["requests"]:
            self.assertTrue({item["reference_id"] for item in request["character_references"]} <= expected_ids)
            self.assertEqual(request["page_script_sha256"], sha256_bytes((ROOT / request["page_script_path"]).read_bytes()))
        self.assertEqual(
            self.blueprint["locked_hashes"]["source_graph"],
            "f3a02b5eebbe4b11035240f64ede32fcf889ff7b85f481dfe11b13744a0fc6b1",
        )

    def test_06_requests_are_scene_specific_and_concise(self):
        for request in self.blueprint["requests"]:
            self.assertTrue(request["principal_action"])
            self.assertLessEqual(len(request["concise_prompt"]), 1800)
            self.assertIn(request["production_unit"], request["concise_prompt"])
            self.assertTrue(request["required_character_ids"])
            self.assertNotIn("complete source graph", request["concise_prompt"].lower())
            page_script = load_json(ROOT / request["page_script_path"])
            self.assertEqual(request["event_ids"], page_script["event_ids"])

    def test_07_indian_cultural_authenticity_and_forbidden_equipment(self):
        result = validate_cultural_authenticity(ROOT)
        self.assertEqual(result["status"], "PASS")
        policy = load_json(ROOT / "book-factory" / "policies" / "indian-cultural-authenticity.json")
        labels = " ".join(item["label"].lower() for item in policy["explicit_foreign_style_exclusions"])
        for item in ("corinthian", "roman", "trojan", "spartan", "medieval", "viking", "western fantasy", "rpg"):
            self.assertIn(item, labels)
        battle = next(item for item in self.blueprint["requests"] if item["proof_id"] == "dm04-proof-battle")
        exclusions = " ".join(battle["prohibited_transfers"]).lower()
        self.assertIn("red-crested greco-roman helmet", exclusions)
        self.assertIn("demonic-face flag", exclusions)

    def test_08_transformation_sequence_is_event_bound(self):
        iconography = load_json(ROOT / "book-factory" / "contracts" / "source-bound-iconography.json")
        mahisha = iconography["requirements"]["mahishasura"]
        self.assertEqual(
            [item["manifestation_id"] for item in mahisha["event_sequence"]],
            [
                "dm-mahisha-buffalo",
                "dm-mahisha-lion",
                "dm-mahisha-armed-man",
                "dm-mahisha-elephant",
                "dm-mahisha-buffalo",
                "dm-mahisha-partial-emergence",
            ],
        )
        self.assertIn("separate locked panels", mahisha["sequence_rule"])
        decisive = next(item for item in self.blueprint["requests"] if item["proof_id"] == "dm04-proof-full-page")
        constraints = " ".join(decisive["source_iconography_constraints"]).lower()
        self.assertIn("half-emerged asura", constraints)
        self.assertIn("buffalo mouth", constraints)
        self.assertIn("buffalo neck", constraints)

    def test_09_character_panel_and_immersive_units_are_distinct(self):
        units = load_json(ROOT / "book-factory" / "contracts" / "visual-production-units.json")
        self.assertEqual({item["type"] for item in units["units"]}, PRODUCTION_UNITS)
        assignment = {item["proof_id"]: item["production_unit"] for item in self.blueprint["requests"]}
        self.assertEqual(Counter(assignment.values()), Counter({"PANEL_ILLUSTRATION": 2, "FULL_PAGE_IMMERSIVE": 2}))

    def test_10_actual_lettering_geometry_is_bound(self):
        result = validate_lettering_and_units(ROOT)
        self.assertEqual(result, {"status": "PASS", "production_units": 3, "geometry_records": 4})
        lettering = load_json(ROOT / "book-factory" / "contracts" / "lettering-composition.json")
        self.assertFalse(lettering["artwork"]["permanent_text"])
        for item in lettering["dm04_recovery_geometry"].values():
            self.assertTrue(item["text"])

    def test_11_comparative_review_requires_independent_image_reviewer(self):
        contract = load_json(ROOT / "book-factory" / "contracts" / "comparative-visual-review.json")
        self.assertIn("image-capable independent reviewer", contract["semantic_boundary"])
        self.assertIn("Deterministic code validates", contract["semantic_boundary"])
        reviewer = self.comparison["reviewer"]
        self.assertTrue(reviewer["image_capable"])
        self.assertTrue(reviewer["independent_from_pr6_producer"])
        self.assertNotEqual(reviewer["id"], reviewer["pr6_producer_id"])

    def test_12_gold_standard_comparison_record_integrity(self):
        result = validate_comparison(ROOT)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["records"], 8)
        for record in self.comparison["records"]:
            self.assertEqual(record["overall"], "FIX")
            self.assertEqual(tuple(item["dimension"] for item in record["dimensions"]), COMPARATIVE_DIMENSIONS)
            self.assertEqual(sha256_bytes((ROOT / record["image_path"]).read_bytes()), record["image_sha256"])

    def test_13_recovery_approval_and_artifact_hash_binding(self):
        payload = build_recovery_payload(ROOT, "DM04")
        stored = ProofRecoveryRequestVersionStore(BOOKS).versions("DM04")
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0]["payload"], payload)
        self.assertFalse(payload["generation_authorized"])
        for request in payload["requests"]:
            self.assertEqual(request["campaign_id"], payload["campaign_id"])
            self.assertFalse(request["generation_authorized"])
            for reference in request["reference_package"]:
                if reference["path"]:
                    self.assertEqual(sha256_bytes((ROOT / reference["path"]).read_bytes()), reference["sha256"])

    def test_14_retry_exhaustion_persists(self):
        events = ProofExecutionLedger(BOOKS, "DM04").events()
        intents = [item for item in events if item["status"] == "INTENT_RECORDED"]
        successes = [item for item in events if item["status"] == "SUCCEEDED"]
        self.assertEqual(len(intents), 8)
        self.assertEqual(len(successes), 8)
        self.assertEqual(set(Counter(item["proof_id"] for item in intents).values()), {2})
        self.assertTrue(self.blueprint["pr6_history"]["retry_ceiling_exhausted"])
        self.assertFalse(self.blueprint["pr6_history"]["counter_reset"])

    def test_15_unauthorized_generation_and_dm08_recovery_are_prevented(self):
        before = (BOOKS / "DM04" / "illustration-proofs" / "generation-ledger.jsonl").read_bytes()
        with self.assertRaises(ContractError):
            FactoryDirector(ROOT).prepare_proof_generation("DM04", "dm04-proof-battle")
        self.assertEqual(before, (BOOKS / "DM04" / "illustration-proofs" / "generation-ledger.jsonl").read_bytes())
        with self.assertRaises(ContractError):
            build_recovery_payload(ROOT, "DM08")

    def test_16_recovery_validation_and_exact_four_requests(self):
        result = validate_recovery_requests(ROOT)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["requests"], 4)
        self.assertFalse(result["generation_authorized"])
        first = FactoryDirector(ROOT).prepare_proof_recovery("DM04")
        second = FactoryDirector(ROOT).prepare_proof_recovery("DM04")
        self.assertEqual(first["version_hash"], second["version_hash"])
        self.assertEqual(len(ProofRecoveryRequestVersionStore(BOOKS).versions("DM04")), 1)
        self.assertEqual(self.blueprint["recommended_pr8_budget"]["maximum_total_image_operations"], 4)
        self.assertEqual(self.blueprint["recommended_pr8_budget"]["authorization_status"], "NOT_AUTHORIZED")

    def test_17_source_graph_is_unchanged(self):
        before = tree_snapshot(GRAPH_ROOT)
        graph = ReadOnlySourceGraph(GRAPH_ROOT).verify()
        self.assertTrue(graph["passed"])
        self.assertEqual(graph["graph_hash"], "f3a02b5eebbe4b11035240f64ede32fcf889ff7b85f481dfe11b13744a0fc6b1")
        self.assertEqual(before, tree_snapshot(GRAPH_ROOT))

    def test_18_pr7_validation_and_existing_factory_regression(self):
        direct = validate_pr7(ROOT, require_source_assets=True)
        self.assertEqual(direct["status"], "PASS")
        self.assertFalse(direct["generation_executed"])
        result = FactoryDirector(ROOT).validate()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["pr7"]["status"], "PASS")
        self.assertEqual(result["reference_editions"][0]["edition_status"], "EXISTING_EDITION")


if __name__ == "__main__":
    unittest.main()
