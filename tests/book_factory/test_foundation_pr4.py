import copy
import json
import tempfile
import unittest
from pathlib import Path

from book_factory.budgets import BudgetGuard
from book_factory.catalogue import CatalogueStore
from book_factory.director import FactoryDirector
from book_factory.drafting import targeted_revision_request
from book_factory.editorial import REQUIRED_SEMANTIC_DIMENSIONS, editorial_review
from book_factory.errors import BudgetExceededError, ContractError
from book_factory.handoffs import MECHANISM, SessionHandoffStore, validate_execution
from book_factory.narrative import validate_manuscript
from book_factory.source_clearance import PRIVATE_DRAFT_OPEN, SourceClearanceStore
from book_factory.source_graph import ReadOnlySourceGraph
from book_factory.util import load_json, tree_snapshot
from book_factory.versioning import EditorialReviewStore, ManuscriptVersionStore


ROOT = Path(__file__).resolve().parents[2]
BOOKS = ROOT / "books"
PACKET_HASH = "b784b365d9c921312285f453b4f6a4a15a7be935e2f0fdda6cfa8eba12797744"
EVENT_IDS = ["dm-event-%03d" % number for number in range(8, 24)]


class FoundationPR4Tests(unittest.TestCase):
    def setUp(self):
        # PR4 evidence remains pinned to immutable v2 even after later milestones.
        self.manuscript_record = ManuscriptVersionStore(BOOKS).versions("DM04")[1]
        self.manuscript = self.manuscript_record["payload"]
        self.packet = load_json(BOOKS / "DM04" / "story-packets" / (PACKET_HASH + ".json"))
        self.allowed_evidence = [item["id"] for item in self.packet["citations"]]
        self.event_evidence = {
            item["id"]: item.get("evidence_ids", []) for item in self.packet["events"]
        }

    def test_private_draft_clearance_does_not_override_source_or_publication(self):
        clearance = SourceClearanceStore(BOOKS).latest("DM04")
        dossier = load_json(BOOKS / "DM04" / "source-readiness" / (clearance["dossier_hash"] + ".json"))
        self.assertEqual(clearance["private_draft_gate"], PRIVATE_DRAFT_OPEN)
        self.assertEqual(clearance["publication_gate"], "BLOCKED")
        self.assertEqual(dossier["status"], "BLOCKED")
        self.assertEqual(dossier["publication_readiness"], "NOT_CERTIFIED")
        self.assertFalse(clearance["rights_determination"]["legal_opinion"])
        self.assertEqual(clearance["rights_determination"]["modern_web_presentation_reuse"], "PROHIBITED")
        self.assertTrue(clearance["independent_source_review"]["executed"])

    def test_real_codex_handoff_and_direct_provider_routing_are_honest(self):
        status = FactoryDirector(ROOT).status()
        self.assertTrue(status["codex_session_handoff"]["supported"])
        self.assertFalse(status["codex_session_handoff"]["programmatic_repository_spawn"])
        self.assertFalse(status["providers"]["manuscript_generation"]["available"])
        self.assertEqual(FactoryDirector(ROOT).draft_manuscript("DM04", True)["status"], "BLOCKED_PROVIDER")
        responses = list((BOOKS / "DM04" / "handoffs" / "manuscript-generation").glob("*.response.json"))
        self.assertEqual(len(responses), 1)
        response = load_json(responses[0])
        self.assertEqual(response["execution"]["mechanism"], MECHANISM)
        self.assertEqual(response["execution"]["paid_api_calls"], 0)
        self.assertEqual(response["execution"]["cost_minor_units"], 0)

    def test_complete_dm04_manuscript_event_coverage_and_provenance(self):
        versions = ManuscriptVersionStore(BOOKS).versions("DM04")
        self.assertGreaterEqual(len(versions), 2)
        self.assertEqual(versions[1]["parent_hash"], versions[0]["content_hash"])
        self.assertTrue(self.manuscript["complete_narrative"])
        self.assertEqual({item["event_id"] for item in self.manuscript["event_coverage"]}, set(EVENT_IDS))
        self.assertEqual(set(self.manuscript["source_packet_hashes"]), {PACKET_HASH})
        check = validate_manuscript(
            self.manuscript,
            EVENT_IDS,
            allowed_evidence_ids=self.allowed_evidence,
            expected_packet_hashes=[PACKET_HASH],
            event_evidence_map=self.event_evidence,
        )
        self.assertEqual(check["result"], "PASS")
        self.assertTrue((BOOKS / "DM04" / "manuscripts" / "v0001.md").is_file())
        self.assertTrue((BOOKS / "DM04" / "manuscripts" / "v0001.event-coverage.json").is_file())
        self.assertTrue((BOOKS / "DM04" / "manuscripts" / "v0001.claim-provenance.json").is_file())
        self.assertTrue((BOOKS / "DM04" / "manuscripts" / "v0002.md").is_file())
        self.assertTrue((BOOKS / "DM04" / "manuscripts" / "v0002.event-coverage.json").is_file())
        self.assertTrue((BOOKS / "DM04" / "manuscripts" / "v0002.claim-provenance.json").is_file())

    def test_editorial_fix_revision_pass_and_separated_statuses(self):
        manuscripts = ManuscriptVersionStore(BOOKS).versions("DM04")
        reviews = EditorialReviewStore(BOOKS).versions("DM04")[:2]
        self.assertEqual([item["payload"]["result"] for item in reviews], ["FIX", "PASS"])
        self.assertEqual(reviews[1]["parent_hash"], reviews[0]["content_hash"])
        self.assertEqual(reviews[0]["payload"]["reviewed_manuscript_hash"], manuscripts[0]["content_hash"])
        self.assertEqual(reviews[1]["payload"]["reviewed_manuscript_hash"], manuscripts[1]["content_hash"])
        self.assertEqual(reviews[1]["payload"]["reviewed_packet_hashes"], [PACKET_HASH])
        self.assertNotEqual(
            reviews[1]["payload"]["reviewer"]["id"],
            manuscripts[1]["payload"]["creator"]["id"],
        )
        self.assertEqual(len(reviews[0]["payload"]["findings"]), 4)
        self.assertEqual(reviews[1]["payload"]["findings"], [])
        self.assertEqual(
            {item["dimension"] for item in reviews[1]["payload"]["dimension_assessments"]},
            REQUIRED_SEMANTIC_DIMENSIONS,
        )
        self.assertTrue(all(item["result"] == "PASS" for item in reviews[1]["payload"]["dimension_assessments"]))
        reviewer = dict(reviews[1]["payload"])
        reviewer.update(reviews[1]["payload"]["reviewer"])
        gate = editorial_review(
            manuscripts[1]["payload"],
            EVENT_IDS,
            reviewer,
            manuscript_hash=manuscripts[1]["content_hash"],
            packet_hashes=[PACKET_HASH],
            allowed_evidence_ids=self.allowed_evidence,
            event_evidence_map=self.event_evidence,
        )
        self.assertEqual(gate["result"], "PASS")
        status = FactoryDirector(ROOT).manuscript_status("DM04")["production_status"]
        self.assertTrue(status["exact_result"] in {
            "PRIVATE_MANUSCRIPT_EDITORIALLY_REVIEWED_PUBLICATION_BLOCKED",
            "MANUSCRIPT_V3_COMPLETE_AWAITING_DUAL_INDEPENDENT_REVIEW_PUBLICATION_BLOCKED",
            "MANUSCRIPT_V3_REQUIRES_REVISION_PUBLICATION_BLOCKED",
            "MANUSCRIPT_V3_AWAITING_SECOND_INDEPENDENT_REVIEW_PUBLICATION_BLOCKED",
            "MANUSCRIPT_V3_DUAL_REVIEWED_VISUAL_PREPRODUCTION_PENDING_PUBLICATION_BLOCKED",
            "VISUAL_PREPRODUCTION_REVIEWED_PUBLICATION_BLOCKED",
            "ILLUSTRATION_PROOFS_REVIEWED_FIX_RETRY_EXHAUSTED_PUBLICATION_BLOCKED",
        } or status["exact_result"].startswith("MANUSCRIPT_PR5_"))
        self.assertEqual(status["source_readiness"], "BLOCKED")
        self.assertIn(status["manuscript_draft_completion"], {"COMPLETE", "COMPLETE_PR5_LATEST_REVISION"})
        self.assertIn(status["independent_editorial_review"], {"PASS", "AWAITING_REVIEW", "FIX", "PARTIAL_PASS", "PASS_DUAL_PERSPECTIVE"})
        self.assertIn(status["visual_production"], {
            "NOT_STARTED_PR4_BOUNDARY",
            "NOT_STARTED",
            "NOT_STARTED_PR5_BOUNDARY",
            "PROOFS_ONLY_FULL_BOOK_NOT_STARTED",
        })
        self.assertEqual(status["publication_readiness"], "BLOCKED")

    def test_unsupported_canonical_claim_is_detected(self):
        manuscript = copy.deepcopy(self.manuscript)
        manuscript["claim_map"].append({
            "id": "unsupported-canonical-claim",
            "beat_id": manuscript["beats"][0]["id"],
            "event_id": "dm-event-008",
            "source_class": "MULA",
            "evidence_ids": ["not-in-locked-packet"],
            "claim": "Unsupported fixture claim",
        })
        check = validate_manuscript(
            manuscript,
            EVENT_IDS,
            allowed_evidence_ids=self.allowed_evidence,
            expected_packet_hashes=[PACKET_HASH],
            event_evidence_map=self.event_evidence,
        )
        self.assertEqual(check["result"], "FIX")
        self.assertIn("UNKNOWN_EVIDENCE_REFERENCE", {item["code"] for item in check["findings"]})

    def test_valid_evidence_from_the_wrong_event_is_detected(self):
        manuscript = copy.deepcopy(self.manuscript)
        manuscript["claim_map"][0]["evidence_ids"] = ["dm-evidence-009"]
        check = validate_manuscript(
            manuscript,
            EVENT_IDS,
            allowed_evidence_ids=self.allowed_evidence,
            expected_packet_hashes=[PACKET_HASH],
            event_evidence_map=self.event_evidence,
        )
        self.assertEqual(check["result"], "FIX")
        self.assertIn("EVIDENCE_OUTSIDE_CLAIM_EVENT", {item["code"] for item in check["findings"]})

    def test_reviewer_independence_and_hash_binding_cannot_be_fabricated(self):
        writer_id = self.manuscript["creator"]["id"]
        reviewer = {
            "id": writer_id,
            "independent": True,
            "capability_verified": True,
            "provider_kind": "editorial_review",
            "reviewed_manuscript_hash": self.manuscript_record["content_hash"],
            "reviewed_packet_hashes": [PACKET_HASH],
            "reviewed_dimensions": sorted(REQUIRED_SEMANTIC_DIMENSIONS),
            "result": "PASS",
            "findings": [],
        }
        result = editorial_review(
            self.manuscript,
            EVENT_IDS,
            reviewer,
            manuscript_hash=self.manuscript_record["content_hash"],
            packet_hashes=[PACKET_HASH],
            allowed_evidence_ids=self.allowed_evidence,
        )
        self.assertEqual(result["result"], "ESCALATE")
        reviewer["id"] = "independent-reviewer"
        reviewer["reviewed_manuscript_hash"] = self.manuscript_record["content_hash"]
        result = editorial_review(
            self.manuscript,
            EVENT_IDS,
            reviewer,
            manuscript_hash=self.manuscript_record["content_hash"],
            packet_hashes=[PACKET_HASH],
            allowed_evidence_ids=self.allowed_evidence,
            event_evidence_map=self.event_evidence,
        )
        self.assertEqual(result["result"], "ESCALATE")
        self.assertIn("SEMANTIC_PASS_ASSESSMENTS_INCOMPLETE", {item["code"] for item in result["findings"]})
        reviewer["reviewed_manuscript_hash"] = "0" * 64
        result = editorial_review(
            self.manuscript,
            EVENT_IDS,
            reviewer,
            manuscript_hash=self.manuscript_record["content_hash"],
            packet_hashes=[PACKET_HASH],
            allowed_evidence_ids=self.allowed_evidence,
        )
        self.assertEqual(result["result"], "ESCALATE")

    def test_failed_review_yields_targeted_revision_and_versions_preserve_parents(self):
        reviewer = {
            "id": "independent-reviewer",
            "independent": True,
            "capability_verified": True,
            "provider_kind": "editorial_review",
            "reviewed_manuscript_hash": self.manuscript_record["content_hash"],
            "reviewed_packet_hashes": [PACKET_HASH],
            "reviewed_dimensions": sorted(REQUIRED_SEMANTIC_DIMENSIONS),
            "result": "FIX",
            "findings": [{
                "code": "FIXTURE_PACING",
                "section_ids": [self.manuscript["beats"][0]["id"]],
                "excerpt": "bounded fixture excerpt",
            }],
        }
        gate = editorial_review(
            self.manuscript,
            EVENT_IDS,
            reviewer,
            manuscript_hash=self.manuscript_record["content_hash"],
            packet_hashes=[PACKET_HASH],
            allowed_evidence_ids=self.allowed_evidence,
        )
        gate.update({
            "book_id": "DM04",
            "review_hash": "a" * 64,
            "reviewed_manuscript_hash": self.manuscript_record["content_hash"],
        })
        revision = targeted_revision_request(gate)
        self.assertEqual(revision["finding_ids"], ["FIXTURE_PACING"])
        with tempfile.TemporaryDirectory() as temporary:
            first = ManuscriptVersionStore(temporary).put("fictional", {"text": "rejected"})
            second = ManuscriptVersionStore(temporary).put("fictional", {"text": "revised"}, first["content_hash"])
            self.assertEqual(second["parent_hash"], first["content_hash"])
            self.assertEqual(len(ManuscriptVersionStore(temporary).versions("fictional")), 2)

    def test_zero_cost_cap_and_retry_configuration(self):
        policy = load_json(ROOT / "book-factory" / "policies" / "spending-policy.json")
        guard = BudgetGuard(policy)
        self.assertEqual(guard.reserve("zero-cost-handoff", 0)["reserved_minor_units"], 0)
        with self.assertRaises(BudgetExceededError):
            guard.reserve("paid-call", 1)
        self.assertEqual(FactoryDirector(ROOT)._configuration()["retry_limits"]["qa_repair"], 3)

    def test_handoff_rejects_self_review_and_nonzero_cost(self):
        with tempfile.TemporaryDirectory() as temporary:
            store = SessionHandoffStore(temporary)
            handoff, _ = store.prepare(
                "fictional", "EDITORIAL_REVIEW", {"request_hash": "a" * 64}, "family-editor", ["b" * 64], writer_id="writer"
            )
            response = {
                "handoff_hash": handoff["handoff_hash"],
                "request_hash": handoff["request_hash"],
                "orchestrator_attested": True,
                "execution": {
                    "mechanism": MECHANISM,
                    "agent_id": "writer",
                    "capability": "editorial_review",
                    "executed": True,
                    "paid_api_calls": 0,
                    "cost_minor_units": 0,
                    "attestation_scope": "ORCHESTRATOR_SESSION_RECORD_NOT_CRYPTOGRAPHIC_IDENTITY",
                },
            }
            with self.assertRaises(ContractError):
                validate_execution(handoff, response, "editorial_review", writer_id="writer")
            response["execution"]["agent_id"] = "reviewer"
            response["execution"]["cost_minor_units"] = 1
            with self.assertRaises(ContractError):
                validate_execution(handoff, response, "editorial_review", writer_id="writer")

    def test_dm08_has_no_new_production_artifacts(self):
        dm08 = CatalogueStore(BOOKS / "catalogue.json").get("DM08")
        self.assertEqual(dm08["edition_status"], "EXISTING_EDITION")
        self.assertFalse(dm08["automatic_production_eligible"])
        self.assertFalse((BOOKS / "DM08" / "manuscripts").exists())
        self.assertFalse((BOOKS / "DM08" / "handoffs").exists())
        with self.assertRaises(ContractError):
            FactoryDirector(ROOT).prepare_manuscript_handoff("DM08")

    def test_read_only_source_graph_is_unchanged_by_status_and_validation(self):
        graph_root = ROOT / "research" / "source-graph"
        before = tree_snapshot(graph_root)
        FactoryDirector(ROOT).manuscript_status("DM04")
        FactoryDirector(ROOT).validate()
        self.assertEqual(before, tree_snapshot(graph_root))
        self.assertEqual(ReadOnlySourceGraph(graph_root).graph_hash(), "f3a02b5eebbe4b11035240f64ede32fcf889ff7b85f481dfe11b13744a0fc6b1")

    def test_resume_after_handoff_interruption_is_idempotent(self):
        events_path = BOOKS / "DM04" / "run" / "events.jsonl"
        before = events_path.read_bytes()
        first = FactoryDirector(ROOT).resume("DM04")
        second = FactoryDirector(ROOT).resume("DM04")
        self.assertEqual(first, second)
        self.assertIn(first["status"], {
            "AWAITING_INDEPENDENT_EDITOR",
            "AWAITING_CODEX_REVISION_AGENT",
            "PRIVATE_MANUSCRIPT_REVISION_COMPLETE_AWAITING_INDEPENDENT_REREVIEW_PUBLICATION_BLOCKED",
            "PRIVATE_MANUSCRIPT_REQUIRES_REVISION_PUBLICATION_BLOCKED",
            "PRIVATE_MANUSCRIPT_EDITORIALLY_REVIEWED_PUBLICATION_BLOCKED",
            "PRIVATE_MANUSCRIPT_ESCALATED_PUBLICATION_BLOCKED",
            "MANUSCRIPT_V3_COMPLETE_AWAITING_DUAL_INDEPENDENT_REVIEW_PUBLICATION_BLOCKED",
            "MANUSCRIPT_V3_AWAITING_SECOND_INDEPENDENT_REVIEW_PUBLICATION_BLOCKED",
            "MANUSCRIPT_V3_DUAL_REVIEWED_VISUAL_PREPRODUCTION_PENDING_PUBLICATION_BLOCKED",
            "MANUSCRIPT_PR5_LATEST_REVISION_DUAL_REVIEWED_VISUAL_PREPRODUCTION_PENDING_PUBLICATION_BLOCKED",
            "VISUAL_PREPRODUCTION_REVIEWED_PUBLICATION_BLOCKED",
            "ILLUSTRATION_PROOFS_REVIEWED_FIX_RETRY_EXHAUSTED_PUBLICATION_BLOCKED",
        })
        self.assertEqual(before, events_path.read_bytes())


if __name__ == "__main__":
    unittest.main()
