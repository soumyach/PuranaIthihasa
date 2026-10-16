import copy
import tempfile
import unittest
from pathlib import Path

from book_factory.approvals import ApprovalStore
from book_factory.bibles import validate_character_bible, validate_location_bible
from book_factory.director import FactoryDirector
from book_factory.editorial import PR5_REVIEW_PERSPECTIVES
from book_factory.errors import ContractError
from book_factory.narrative import validate_manuscript
from book_factory.preproduction import ProofStageStore, validate_storyboard
from book_factory.source_graph import ReadOnlySourceGraph
from book_factory.state import page_id
from book_factory.util import content_hash, load_json, sha256_bytes, tree_snapshot
from book_factory.versioning import (
    CharacterBibleVersionStore,
    EditorialReviewStore,
    LocationBibleVersionStore,
    ManuscriptVersionStore,
    ProofSpecVersionStore,
    StoryboardVersionStore,
    TypographyVersionStore,
)


ROOT = Path(__file__).resolve().parents[2]
BOOKS = ROOT / "books"
PACKET_HASH = "b784b365d9c921312285f453b4f6a4a15a7be935e2f0fdda6cfa8eba12797744"
EVENT_IDS = ["dm-event-%03d" % number for number in range(8, 24)]
PR4_MANUSCRIPT_HASHES = [
    "7979c89ca4d7f227bfab91c42c9191b269502e457bdeb3dd08e4ccee2827c4ba",
    "40d02a77dedf68f8b9e216822293b8a5911ba9be8c644fe8ca6d434efbdba1fa",
]


class FoundationPR5AcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.manuscripts = ManuscriptVersionStore(BOOKS).versions("DM04")
        self.v3_record = self.manuscripts[2]
        self.v3 = self.v3_record["payload"]
        self.latest_record = self.manuscripts[-1]
        self.latest = self.latest_record["payload"]
        self.packet = load_json(BOOKS / "DM04" / "story-packets" / (PACKET_HASH + ".json"))
        self.character = CharacterBibleVersionStore(BOOKS).versions("DM04")[-1]["payload"]
        self.location = LocationBibleVersionStore(BOOKS).versions("DM04")[-1]["payload"]
        self.storyboard = StoryboardVersionStore(BOOKS).versions("DM04")[-1]["payload"]
        self.proofs = ProofSpecVersionStore(BOOKS).versions("DM04")[-1]["payload"]
        self.typography = TypographyVersionStore(BOOKS).versions("DM04")[-1]["payload"]

    def test_01_v3_preserves_all_events_and_prior_versions(self):
        self.assertGreaterEqual(len(self.manuscripts), 3)
        self.assertEqual([item["content_hash"] for item in self.manuscripts[:2]], PR4_MANUSCRIPT_HASHES)
        self.assertEqual(self.v3_record["parent_hash"], PR4_MANUSCRIPT_HASHES[1])
        self.assertEqual({item["event_id"] for item in self.v3["event_coverage"]}, set(EVENT_IDS))
        self.assertEqual({event for beat in self.v3["beats"] for event in beat["event_ids"]}, set(EVENT_IDS))

    def test_02_unsupported_claims_are_rejected(self):
        changed = copy.deepcopy(self.latest)
        changed["claim_map"].append({
            "id": "unsupported-pr5", "beat_id": "beat-008", "event_id": "dm-event-008",
            "source_class": "MULA", "evidence_ids": ["outside-locked-packet"], "claim": "unsupported",
        })
        gate = validate_manuscript(
            changed, EVENT_IDS,
            allowed_evidence_ids=[item["id"] for item in self.packet["citations"]],
            expected_packet_hashes=[PACKET_HASH],
            event_evidence_map={item["id"]: item["evidence_ids"] for item in self.packet["events"]},
        )
        self.assertEqual(gate["result"], "FIX")
        self.assertIn("UNKNOWN_EVIDENCE_REFERENCE", {item["code"] for item in gate["findings"]})

    def test_03_two_independent_reviewers_cannot_self_certify(self):
        reviews = [
            item["payload"] for item in EditorialReviewStore(BOOKS).versions("DM04")
            if item["payload"].get("reviewed_manuscript_hash") == self.latest_record["content_hash"]
        ]
        self.assertEqual({item["review_perspective"] for item in reviews}, set(PR5_REVIEW_PERSPECTIVES))
        self.assertTrue(all(item["result"] == "PASS" for item in reviews))
        self.assertTrue(all(item["reviewer"]["id"] != self.latest["creator"]["id"] for item in reviews))
        self.assertEqual(len({item["reviewer"]["id"] for item in reviews}), 2)

    def test_04_storyboard_event_character_speaker_and_order_integrity(self):
        gate = validate_storyboard(
            self.storyboard, EVENT_IDS, self.latest, self.character, self.location,
            self.latest_record["content_hash"],
        )
        self.assertEqual(gate["result"], "PASS", gate["findings"])
        covered = {event for page in self.storyboard["pages"] for event in page["event_ids"]}
        self.assertEqual(covered, set(EVENT_IDS))
        character_ids = [item["id"] for item in self.character["entries"]]
        self.assertEqual(len(character_ids), len(set(character_ids)))
        self.assertTrue(all(
            item.get("speaker_id") in character_ids
            for page in self.storyboard["pages"] for item in page["lettering"]
            if item["channel"] in {"DIALOGUE", "THOUGHT"}
        ))
        for number, page in enumerate(self.storyboard["pages"], 1):
            self.assertEqual(page["page_number"], number)
            self.assertEqual(page["page_id"], page_id("DM04", number))
            self.assertTrue(all(panel["image_instructions"].get("required_action") for panel in page["panels"]))
            self.assertFalse(any(
                panel["visual_description"] == "Advance the same sourced action without repeating the lettering."
                for panel in page["panels"]
            ))
            self.assertTrue(all(
                item.get("speaker_id") in page["character_ids"]
                for item in page["lettering"] if item["channel"] in {"DIALOGUE", "THOUGHT"}
            ))
        self.assertIn("thousand arms", " ".join(self.storyboard["pages"][8]["narrative_beats"]))
        self.assertIn("bhindipāla", " ".join(self.storyboard["pages"][20]["narrative_beats"]))
        ending_text = " ".join(item["text"] for page in self.storyboard["pages"][29:] for item in page["lettering"])
        for required in ("reached heaven", "What you have asked shall be granted", "emerge from Gauri"):
            self.assertIn(required, ending_text)

    def test_05_manifestations_remain_distinct(self):
        gate = validate_character_bible(self.character)
        self.assertEqual(gate["result"], "PASS", gate["findings"])
        owners = {}
        for entry in self.character["entries"]:
            for form in entry["manifestation_rules"]:
                self.assertNotIn(form["manifestation_id"], owners)
                owners[form["manifestation_id"]] = entry["id"]
        mahisha = next(item for item in self.character["entries"] if item["id"] == "dm-mahisha")
        self.assertEqual(
            {item["manifestation_id"] for item in mahisha["manifestation_rules"]},
            {"dm-mahisha-buffalo", "dm-mahisha-lion", "dm-mahisha-armed-man", "dm-mahisha-elephant", "dm-mahisha-partial-emergence"},
        )
        devi = next(item for item in self.character["entries"] if item["id"] == "dm-devi")
        self.assertIn("thousand-arm", devi["arm_count_policy"])
        self.assertTrue({"dm-spear", "dm-rod", "dm-rosary", "dm-waterpot"}.issubset(devi["authorized_weapon_ids"]))
        self.assertTrue(all(item["identity"]["aliases"] for item in self.character["entries"]))
        duplicate = copy.deepcopy(self.character)
        duplicate["entries"][0]["manifestation_rules"].append(
            copy.deepcopy(duplicate["entries"][0]["manifestation_rules"][0])
        )
        duplicate_gate = validate_character_bible(duplicate)
        self.assertIn("DUPLICATE_MANIFESTATION_ID", {item["code"] for item in duplicate_gate["findings"]})

        duplicate_location = copy.deepcopy(self.location)
        duplicate_location["entries"].append(copy.deepcopy(duplicate_location["entries"][0]))
        location_gate = validate_location_bible(duplicate_location)
        self.assertIn("DUPLICATE_LOCATION_ID", {item["code"] for item in location_gate["findings"]})

    def test_06_caption_dialogue_duplication_is_detected(self):
        changed = copy.deepcopy(self.storyboard)
        changed["pages"][0]["lettering"].extend([
            {"id": "dup-n", "channel": "NARRATION", "text": "The same exact line.", "placement": "top"},
            {"id": "dup-d", "channel": "DIALOGUE", "text": "The same exact line.", "speaker_id": "dm-medhas", "placement": "balloon"},
        ])
        gate = validate_storyboard(
            changed, EVENT_IDS, self.latest, self.character, self.location,
            self.latest_record["content_hash"],
        )
        self.assertIn("CAPTION_DIALOGUE_DUPLICATION", {item["code"] for item in gate["findings"]})
        changed["pages"][0]["character_ids"].remove("dm-medhas")
        changed["pages"][0]["panels"][0]["visual_description"] = "Advance the same sourced action without repeating the lettering."
        changed["pages"][0]["panels"][0]["image_instructions"].pop("required_action")
        gate = validate_storyboard(
            changed, EVENT_IDS, self.latest, self.character, self.location,
            self.latest_record["content_hash"],
        )
        codes = {item["code"] for item in gate["findings"]}
        self.assertIn("SPEAKER_NOT_PRESENT_ON_PAGE", codes)
        self.assertIn("PLACEHOLDER_PANEL_SPECIFICATION", codes)
        self.assertIn("PANEL_REQUIRED_ACTION_MISSING", codes)

    def test_07_full_page_immersion_and_proof_provider_block(self):
        self.assertTrue(any(page["layout"]["type"] == "FULL_PAGE" for page in self.storyboard["pages"]))
        self.assertEqual(self.proofs["provider_status"], "BLOCKED_PROVIDER")
        self.assertEqual(len(self.proofs["specs"]), 4)
        self.assertTrue(all(item["status"] == "SPEC_READY_PROVIDER_BLOCKED" for item in self.proofs["specs"]))
        self.assertTrue(all(item["source_support"] for item in self.proofs["specs"]))
        self.assertEqual(self.typography["print_readiness"]["claim"], "NOT_PRINT_READY")
        self.assertTrue(all(
            item["licensing_status"] == "NOT_VERIFIED_FOR_BUNDLING"
            and item["inspection_basis"] == "SYSTEM_INSTALLED_REFERENCE_ONLY"
            for item in self.typography["font_candidates"]
        ))
        status = FactoryDirector(ROOT).status()
        self.assertFalse(status["providers"]["image"]["available"])
        self.assertFalse(status["providers"]["visual_evaluation"]["available"])

    def test_08_visual_approval_does_not_cross_to_unrelated_character(self):
        with tempfile.TemporaryDirectory() as temporary:
            store = ApprovalStore(temporary)
            approved_hash = content_hash({"character_id": "dm-devi", "version": 1})
            other_hash = content_hash({"character_id": "dm-mahisha", "version": 1})
            store.create(
                "CHARACTER_FAMILY", "CHARACTER_VARIANT", approved_hash,
                {"type": "character_family", "id": "dm-devi-family"},
                {"id": "reviewer"}, {"id": "artist"}, "PASS",
                inheritance_allowed=True,
                source_scope="DM04", tradition_id="devi-mahatmya", edition_id="locked-packet",
            )
            self.assertIsNone(store.find_valid(
                "CHARACTER_VARIANT", other_hash,
                {"type": "character_family", "id": "dm-mahisha-family", "ancestors": ["dm-devi-family"]},
                target_context={"source_scope": "DM04", "tradition_id": "devi-mahatmya", "edition_id": "locked-packet"},
                current_evidence_hash=other_hash,
            ))

    def test_09_proof_retry_limit_is_enforced(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            store = ProofStageStore(root, retry_limit=2)
            package = copy.deepcopy(self.proofs)
            record = store.initialize("DM04", package)
            image = root / "candidate.png"
            image.write_bytes(b"synthetic-test-proof")
            digest = sha256_bytes(image.read_bytes())
            proof_id = package["specs"][0]["id"]
            store.record_attempt("DM04", proof_id, image, digest, "fixture-1")
            store.reject("DM04", proof_id, "reviewer", ["fixture rejection"])
            store.record_attempt("DM04", proof_id, image, digest, "fixture-2")
            store.reject("DM04", proof_id, "reviewer", ["fixture rejection"])
            with self.assertRaises(ContractError):
                store.record_attempt("DM04", proof_id, image, digest, "fixture-3")
            self.assertIsNotNone(record["content_hash"])

    def test_10_source_graph_and_dm08_remain_untouched(self):
        graph_root = ROOT / "research" / "source-graph"
        before = tree_snapshot(graph_root)
        self.assertEqual(ReadOnlySourceGraph(graph_root).graph_hash(), "f3a02b5eebbe4b11035240f64ede32fcf889ff7b85f481dfe11b13744a0fc6b1")
        FactoryDirector(ROOT).validate()
        self.assertEqual(before, tree_snapshot(graph_root))
        self.assertFalse((BOOKS / "DM08" / "manuscripts").exists())
        self.assertFalse((BOOKS / "DM08" / "handoffs").exists())


if __name__ == "__main__":
    unittest.main()
