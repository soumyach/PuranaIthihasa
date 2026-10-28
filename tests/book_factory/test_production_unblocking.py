import copy
import tempfile
import unittest
from pathlib import Path

from book_factory.director import FactoryDirector
from book_factory.errors import ContractError
from book_factory.handoffs import MECHANISM, SessionHandoffStore, validate_execution
from book_factory.reconciliation import ProductionStateReconciler
from book_factory.util import load_json, tree_snapshot


ROOT = Path(__file__).resolve().parents[2]


def specialist_response(handoff, agent_id, capability):
    return {
        "schema_version": "1.0",
        "handoff_hash": handoff["handoff_hash"],
        "request_hash": handoff["request_hash"],
        "orchestrator_attested": True,
        "execution": {
            "mechanism": MECHANISM,
            "executed": True,
            "capability": capability,
            "agent_id": agent_id,
            "paid_api_calls": 0,
            "cost_minor_units": 0,
            "attestation_scope": "ORCHESTRATOR_SESSION_RECORD_NOT_CRYPTOGRAPHIC_IDENTITY",
        },
        "result": {"verdict": "PASS"},
    }


class ProductionReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.reconciler = ProductionStateReconciler(ROOT)

    def test_actual_dm02_campaign_and_invalidation_reconcile(self):
        state = self.reconciler.reconcile("DM02", persist=False)
        self.assertEqual(state["current_stage"], "ILLUSTRATION")
        self.assertEqual(state["campaign"]["total_executed"], 39)
        self.assertEqual(state["campaign"]["total_ceiling"], 43)
        self.assertEqual(state["campaign"]["operations_authorized_for_resume"], 0)
        self.assertEqual(state["pages"]["recorded_complete_before_invalidation"], [
            2, 3, 7, 8, 9, 13, 14, 15, 16, 17, 18, 21, 22, 23, 24,
        ])
        self.assertEqual(state["pages"]["effective_complete"], [2, 3, 22, 23, 24])
        self.assertEqual(len(state["pages"]["blocked"]), 19)
        self.assertEqual(state["page_11"]["status"], "ESCALATE_BEFORE_GENERATION")
        self.assertFalse(state["page_11"]["qualified_review_signed"])
        self.assertIn("p01-panel-01", state["resume_policy"]["candidate_unit_ids_after_required_approvals"])
        self.assertNotIn("p11-panel-01", state["resume_policy"]["candidate_unit_ids_after_required_approvals"])
        self.assertEqual(state["resume_policy"]["separately_gated_unit_ids"], ["p11-panel-01"])

    def test_attempt_counters_and_campaign_scope_are_preserved(self):
        campaign = self.reconciler.reconcile("DM02")["campaign"]
        self.assertEqual(campaign["attempts_by_unit"]["p04-panel-01"], 2)
        self.assertEqual(campaign["repair_attempts_by_unit"]["p04-panel-01"], 1)
        self.assertTrue(all(value <= 2 for value in campaign["attempts_by_unit"].values()))
        self.assertTrue(all(value <= 1 for value in campaign["repair_attempts_by_unit"].values()))
        self.assertTrue(campaign["scope_closed"])
        self.assertEqual(campaign["unspent_conditional_reserve"], 4)

    def test_evidence_hash_tamper_fails_closed(self):
        manifest = copy.deepcopy(load_json(ROOT / "books/DM02/production-reconciliation/evidence.v0001.json"))
        manifest["evidence"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ContractError, "hash mismatch"):
            self.reconciler._evidence(manifest)

    def test_conflicting_manifest_chain_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = root / "books/DM02/production-reconciliation"
            destination.mkdir(parents=True)
            original = load_json(ROOT / "books/DM02/production-reconciliation/evidence.v0001.json")
            from book_factory.util import atomic_json_write
            atomic_json_write(destination / "evidence.v0001.json", original)
            conflicting = copy.deepcopy(original)
            conflicting["sequence"] = 2
            conflicting["supersedes_sha256"] = "0" * 64
            atomic_json_write(destination / "evidence.v0002.json", conflicting)
            with self.assertRaisesRegex(ContractError, "chain is inconsistent"):
                ProductionStateReconciler(root)._load_manifest_chain("DM02")

    def test_resume_and_queue_are_idempotent_and_do_not_touch_production_assets(self):
        observed = {
            "graph": tree_snapshot(ROOT / "research/source-graph"),
            "campaign": tree_snapshot(ROOT / "books/DM02/book-level-production"),
            "dm04": tree_snapshot(ROOT / "books/DM04"),
            "dm08": tree_snapshot(ROOT / "books/DM08"),
        }
        director = FactoryDirector(ROOT)
        first = director.resume_book("DM02")
        second = director.resume_book("DM02")
        queue = director.factory_queue()
        row = next(item for item in queue["entries"] if item["book_id"] == "DM02")
        self.assertEqual(first["status"], "ESCALATE")
        self.assertEqual(second["effective_state_hash"], first["effective_state_hash"])
        self.assertEqual(row["current_stage"], "ILLUSTRATION")
        self.assertEqual(row["queue_status"], "BLOCKED")
        self.assertIn("NEW_CAMPAIGN_AUTHORIZATION_REQUIRED", row["reasons"])
        self.assertEqual(observed["graph"], tree_snapshot(ROOT / "research/source-graph"))
        self.assertEqual(observed["campaign"], tree_snapshot(ROOT / "books/DM02/book-level-production"))
        self.assertEqual(observed["dm04"], tree_snapshot(ROOT / "books/DM04"))
        self.assertEqual(observed["dm08"], tree_snapshot(ROOT / "books/DM08"))


class ActiveCodexHandoffTests(unittest.TestCase):
    def test_actual_host_demo_receipts_are_valid_independent_and_resumable(self):
        demo_root = ROOT / "book-factory/reports/production-unblocking/active-codex-demo"
        specialist_root = demo_root / "DM02/handoffs/director-diagnostic"
        review_root = demo_root / "DM02/handoffs/director-diagnostic-review"
        specialist_handoff = load_json(next(specialist_root.glob("*.request.json")))
        specialist_response = load_json(next(specialist_root.glob("*.response.json")))
        review_handoff = load_json(next(review_root.glob("*.request.json")))
        review_response = load_json(next(review_root.glob("*.response.json")))

        validate_execution(specialist_handoff, specialist_response, "orchestration_diagnostic")
        validate_execution(
            review_handoff,
            review_response,
            "orchestration_diagnostic_review",
            writer_id=specialist_response["execution"]["agent_id"],
        )
        self.assertEqual(specialist_response["result"]["verdict"], "PASS")
        self.assertEqual(review_response["result"]["verdict"], "PASS")
        self.assertNotEqual(
            specialist_response["execution"]["agent_id"],
            review_response["execution"]["agent_id"],
        )
        resumed = SessionHandoffStore(demo_root).resume_status(specialist_handoff)
        self.assertEqual(resumed["status"], "SPECIALIST_RESPONSE_AVAILABLE")
        self.assertFalse(resumed["dispatch_required"])

    def test_interruption_resume_reuses_bound_specialist_response(self):
        with tempfile.TemporaryDirectory() as temporary:
            store = SessionHandoffStore(temporary)
            request = {"request_hash": "a" * 64, "task": "read-only reconciliation diagnostic"}
            handoff, _ = store.prepare(
                "DM02", "DIRECTOR_DIAGNOSTIC", request,
                "production-state-specialist", ["b" * 64],
            )
            pending = store.resume_status(handoff)
            self.assertTrue(pending["dispatch_required"])
            response = specialist_response(handoff, "specialist-agent", "orchestration_diagnostic")
            validate_execution(handoff, response, "orchestration_diagnostic")
            stored, _ = store.store_response(handoff, response)

            rehydrated = SessionHandoffStore(temporary).resume_status(handoff)
            self.assertFalse(rehydrated["dispatch_required"])
            self.assertEqual(rehydrated["response_hash"], stored["response_hash"])
            stored_again, _ = store.store_response(handoff, response)
            self.assertEqual(stored_again["response_hash"], stored["response_hash"])

    def test_independent_reviewer_must_differ_from_specialist(self):
        with tempfile.TemporaryDirectory() as temporary:
            store = SessionHandoffStore(temporary)
            handoff, _ = store.prepare(
                "DM02", "DIRECTOR_DIAGNOSTIC_REVIEW",
                {"request_hash": "c" * 64, "task": "independent review"},
                "independent-orchestration-reviewer", ["d" * 64], writer_id="specialist-agent",
            )
            self_review = specialist_response(
                handoff, "specialist-agent", "orchestration_diagnostic_review",
            )
            with self.assertRaisesRegex(ContractError, "reviewer must differ"):
                validate_execution(
                    handoff, self_review, "orchestration_diagnostic_review",
                    writer_id="specialist-agent",
                )
            independent = specialist_response(
                handoff, "independent-reviewer", "orchestration_diagnostic_review",
            )
            validate_execution(
                handoff, independent, "orchestration_diagnostic_review",
                writer_id="specialist-agent",
            )

    def test_cli_registers_reconciliation_command(self):
        from book_factory.cli import build_parser
        args = build_parser().parse_args(["reconcile-book", "--book-id", "DM02", "--write"])
        self.assertEqual(args.command, "reconcile-book")
        self.assertTrue(args.write)


if __name__ == "__main__":
    unittest.main()
