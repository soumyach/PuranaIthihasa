"""Single user-facing orchestration facade for Foundation PR4."""

import json
from pathlib import Path

from . import __version__
from .catalogue import CatalogueStore
from .catalogue_v01 import SourceMappingRegistry
from .contracts import load_schema, validate_named
from .drafting import (
    build_manuscript_request,
    build_review_request,
    render_manuscript_markdown,
    targeted_revision_request,
)
from .editorial import editorial_review, finalize_review
from .errors import ContractError, NotImplementedStageError
from .handoffs import SessionHandoffStore, finalize_handoff, validate_execution
from .narrative import validate_manuscript
from .pilot import PilotSelector, catalogue_readiness_report
from .providers.base import FixtureImageProviderContract, ProviderRegistry
from .references import ReferenceEditionRegistry
from .rules import rules_status
from .source_graph import ReadOnlySourceGraph
from .source_intelligence import DossierStore, SourceReadinessAssessor, StoryPacketBuilder, StoryPacketStore
from .source_clearance import SourceClearanceStore, finalize_clearance, validate_private_draft_clearance
from .state import StateStore, next_stage
from .util import atomic_json_write, atomic_write, content_hash, load_json, sha256_bytes
from .versioning import EditorialReviewStore, ManuscriptVersionStore


class FactoryDirector:
    def __init__(self, repository_root, catalogue_path=None):
        self.root = Path(repository_root).resolve()
        self.books_root = self.root / "books"
        self.catalogue = CatalogueStore(Path(catalogue_path).resolve() if catalogue_path else self.books_root / "catalogue.json")
        self.graph = ReadOnlySourceGraph(self.root / "research" / "source-graph")
        self.source_intelligence = SourceReadinessAssessor(self.graph, self.root)
        self.providers = ProviderRegistry({"image": FixtureImageProviderContract()})
        self.mappings = SourceMappingRegistry(self.root / "book-factory" / "config" / "catalogue-source-mappings.json")
        self.reference_editions = ReferenceEditionRegistry(self.root)
        self.clearances = SourceClearanceStore(self.books_root)
        self.handoffs = SessionHandoffStore(self.books_root)

    def _configuration(self):
        config = load_json(self.root / "book-factory" / "config" / "defaults.json")
        limits = config["concurrency"]
        if limits.get("max_active_books") != 1:
            raise ContractError("Foundation requires max_active_books = 1")
        if not 1 <= limits.get("max_worker_jobs", 0) <= 3:
            raise ContractError("max_worker_jobs must be between 1 and 3")
        if not 1 <= limits.get("max_image_requests", 0) <= 2:
            raise ContractError("max_image_requests must be between 1 and 2")
        return config

    def status(self):
        books = self.catalogue.list_books()
        states = []
        for path in sorted(self.books_root.glob("*/run/state.json")):
            book_id = path.parents[1].name
            try:
                state = StateStore(self.books_root, book_id).load()
                states.append({"book_id": book_id, "stage": state["current_stage"], "version": state["version"]})
            except ContractError as exc:
                states.append({"book_id": book_id, "status": "INVALID", "message": str(exc)})
        return {
            "factory_version": __version__,
            "implementation": "FOUNDATION_PR4",
            "catalogue_books": len(books),
            "readiness_counts": {state: sum(book["readiness"] == state for book in books) for state in sorted({book["readiness"] for book in books})},
            "active_runs": states,
            "rules": rules_status(self.root),
            "providers": self.providers.capabilities(),
            "codex_session_handoff": {
                "supported": True,
                "programmatic_repository_spawn": False,
                "mechanism": "CODEX_SPECIALIST_SUBAGENT_HANDOFF",
                "identity_assurance": "ORCHESTRATOR_SESSION_ATTESTATION_NOT_CRYPTOGRAPHIC",
                "paid_api_calls": 0,
            },
            "configuration": self._configuration(),
            "publishing": "NOT_IMPLEMENTED",
            "inputs": self.input_report(),
            "dm08_reference_edition": self.reference_editions.verify("DM08"),
        }

    def input_report(self):
        return load_json(self.root / "book-factory" / "reports" / "missing-inputs.json")

    def list_books(self):
        return {"books": self.catalogue.list_books(), "count": len(self.catalogue.list_books())}

    def check_readiness(self, book_id=None):
        before = self.graph.snapshot()
        graph_report = self.graph.verify()
        standards = rules_status(self.root)
        books = self.catalogue.list_books()
        if book_id:
            books = [book for book in books if book["id"] == book_id]
            if not books:
                raise ContractError("book %s is not in the catalogue" % book_id)
        decisions = []
        for book in books:
            dossier = self.source_intelligence.assess(book, self.mappings.resolve(book["id"]))
            blockers = [item["code"] for item in dossier["blockers"]]
            blockers.extend(item["code"] for item in dossier["unresolved_flags"])
            decisions.append({
                "book_id": book["id"],
                "catalogue_readiness": book["readiness"],
                "source_readiness": dossier["status"],
                "dossier_hash": dossier["dossier_hash"],
                "decision": "READY" if not blockers and dossier["status"] == "READY" else "BLOCKED",
                "blockers": blockers,
            })
        result = {
            "graph": {
                "passed": graph_report["passed"],
                "graph_hash": graph_report["graph_hash"],
                "scope": graph_report["scope"],
                "story_spine_statuses": graph_report["counts"]["story_spine_statuses"],
            },
            "standards": standards,
            "books": decisions,
            "catalogue_empty": not bool(self.catalogue.list_books()),
        }
        self.graph.assert_unchanged(before)
        return result

    def source_dossier(self, book_id, write=False):
        manifest = self.catalogue.get(book_id)
        if manifest is None:
            raise ContractError("book %s is not in the catalogue" % book_id)
        before = self.graph.snapshot()
        self.graph.verify()
        dossier = self.source_intelligence.assess(manifest, self.mappings.resolve(book_id))
        validate_named(dossier, self.root / "schemas" / "book-factory", "source-readiness")
        self.graph.assert_unchanged(before)
        if write:
            dossier["stored_at"] = str(DossierStore(self.books_root).put(dossier))
        else:
            dossier["mutated"] = False
        return dossier

    def story_packet(self, spine_id):
        before = self.graph.snapshot()
        self.graph.verify()
        packet = StoryPacketBuilder.build(self.graph.story_packet(spine_id))
        validate_named(packet, self.root / "schemas" / "book-factory", "story-packet")
        self.graph.assert_unchanged(before)
        return packet

    def evaluate_catalogue(self, write=False):
        before = self.graph.snapshot()
        self.graph.verify()
        catalogue = self.catalogue.load()
        mapping_validation = PilotSelector(self.graph, self.mappings).validate_mappings(catalogue["books"])
        ranked_ids = [item["book_id"] for item in self.mappings.pilot_ranking()]
        dossiers = [
            self.source_intelligence.assess(self.catalogue.get(book_id), self.mappings.resolve(book_id))
            for book_id in ranked_ids
        ]
        ranked = PilotSelector(self.graph, self.mappings).rank(catalogue["books"], dossiers)
        report = catalogue_readiness_report(catalogue, mapping_validation, dossiers, ranked)
        self.graph.assert_unchanged(before)
        if write:
            report_path = self.root / "book-factory" / "reports" / "catalogue-readiness.json"
            candidates_path = self.root / "book-factory" / "reports" / "pilot-candidates.json"
            atomic_json_write(report_path, report)
            atomic_json_write(candidates_path, {
                "schema_version": "1.0",
                "strictly_eligible_count": report["strictly_ready_count"],
                "eligibility_note": "No finalist is publication/source certified. These are conditional controlled-production finalists.",
                "candidates": ranked,
                "recommendation": {"book_id": "DM04", "title": self.catalogue.get("DM04")["title"]},
            })
            lines = [
                "# PR3 pilot candidate evaluation",
                "",
                "The catalogue contains 78 books in 12 collections. Strict current eligibility is **0** because rights clearance and independent review remain unresolved. The three entries below are conditional controlled-production finalists, not publication-ready books.",
                "",
            ]
            for item in ranked:
                lines.extend([
                    "## %d. %s — %s" % (item["rank"], item["book_id"], item["title"]),
                    "",
                    item["reason"],
                    "",
                    "Evidence: %d scoped events, %d evidence citations, %d characters/entities, %d boon/power records. Source status: `%s`; pilot status: `%s`; publication status: `%s`." % (
                        item["evidence"]["events"], item["evidence"]["citations"], item["evidence"]["characters"], item["evidence"]["powers"], item["source_readiness"], item["controlled_pilot_eligibility"], item["publication_readiness"],
                    ),
                    "",
                ])
            lines.extend([
                "## Recommendation",
                "",
                "Select **DM04 — The Buffalo King** for the first new-book run. Its exact sixteen-event Mahisha spine is self-contained and visually broad enough to exercise the full factory later. This milestone stops after the dossier and Story Packet; it does not draft, illustrate, typeset, publish, or certify the book.",
                "",
                "DM08 is an existing reference edition and is excluded from automatic selection.",
            ])
            atomic_write(self.root / "book-factory" / "reports" / "pilot-candidates.md", ("\n".join(lines) + "\n").encode("utf-8"))
            report["written"] = [str(report_path), str(candidates_path)]
        return report

    def prepare_pilot(self, book_id):
        manifest = self.catalogue.get(book_id)
        if manifest is None:
            raise ContractError("book %s is not in the catalogue" % book_id)
        if manifest.get("edition_status") == "EXISTING_EDITION" or not manifest.get("automatic_production_eligible", True):
            raise ContractError("existing/reference editions cannot be prepared as automatic production pilots")
        mapping = self.mappings.resolve(book_id)
        dossier = self.source_intelligence.assess(manifest, mapping)
        if dossier["controlled_pilot_eligibility"] == "NOT_ELIGIBLE":
            raise ContractError("book is not eligible even for controlled pilot preparation", {"book_id": book_id})
        dossier_path = DossierStore(self.books_root).put(dossier)
        packet_paths = [str(StoryPacketStore(self.books_root).put(book_id, packet)) for packet in dossier["story_packets"]]
        return {
            "status": "PREPARED_CONDITIONAL",
            "book_id": book_id,
            "dossier_path": str(dossier_path),
            "dossier_hash": dossier["dossier_hash"],
            "story_packet_paths": packet_paths,
            "story_packet_hashes": [item["packet_hash"] for item in dossier["story_packets"]],
            "source_readiness": dossier["status"],
            "publication_readiness": dossier["publication_readiness"],
            "next_stage": "BLOCKED_PROVIDER",
            "generated_manuscript": False,
        }

    def _production_inputs(self, book_id):
        manifest = self.catalogue.get(book_id)
        if manifest is None:
            raise ContractError("book %s is not in the catalogue" % book_id)
        if manifest.get("edition_status") == "EXISTING_EDITION" or not manifest.get("automatic_production_eligible", True):
            raise ContractError("existing/reference editions cannot enter manuscript production")
        dossier = self.source_intelligence.assess(manifest, self.mappings.resolve(book_id))
        packets = dossier["story_packets"]
        return manifest, dossier, packets

    def import_source_clearance(self, book_id, record_path):
        _, dossier, packets = self._production_inputs(book_id)
        record = finalize_clearance(load_json(Path(record_path)))
        validate_named(record, self.root / "schemas" / "book-factory", "source-clearance")
        validate_private_draft_clearance(record, dossier, packets)
        stored, path = self.clearances.put(record)
        return {
            "status": stored["private_draft_gate"],
            "book_id": book_id,
            "clearance_hash": stored["clearance_hash"],
            "path": str(path),
            "publication_gate": stored["publication_gate"],
            "source_readiness_unchanged": dossier["status"],
        }

    def prepare_manuscript_handoff(self, book_id, revision_review_hash=None):
        manifest, dossier, packets = self._production_inputs(book_id)
        clearance = self.clearances.latest(book_id)
        validate_private_draft_clearance(clearance, dossier, packets)
        versions = ManuscriptVersionStore(self.books_root).versions(book_id)
        parent = versions[-1] if versions else None
        revision = None
        kind = "MANUSCRIPT_GENERATION"
        if revision_review_hash:
            reviews = EditorialReviewStore(self.books_root).versions(book_id)
            matching = [item for item in reviews if item["payload"].get("review_hash") == revision_review_hash]
            if not matching:
                raise ContractError("revision review hash is not an immutable review version")
            if matching[-1]["payload"].get("result") != "FIX":
                raise ContractError("only a FIX review can authorize manuscript revision")
            if len(versions) - 1 >= self._configuration()["retry_limits"]["qa_repair"]:
                raise ContractError("manuscript revision retry cap reached")
            revision = targeted_revision_request(matching[-1]["payload"])
            validate_named(revision, self.root / "schemas" / "book-factory", "revision-request")
            kind = "MANUSCRIPT_REVISION"
        elif versions:
            raise ContractError("a manuscript already exists; revision requires an exact FIX review hash")
        request = build_manuscript_request(
            manifest,
            dossier,
            packets,
            dossier["rules_hash"],
            clearance=clearance,
            parent_manuscript=parent,
            revision_request=revision,
        )
        validate_named(request, self.root / "schemas" / "book-factory", "manuscript-request")
        locked = [
            dossier["dossier_hash"], dossier["graph_hash"], dossier["rules_hash"], clearance["clearance_hash"],
            *[packet["packet_hash"] for packet in packets],
        ]
        if parent:
            locked.append(parent["content_hash"])
        handoff, path = self.handoffs.prepare(book_id, kind, request, "manuscript-story", locked)
        store = StateStore(self.books_root, book_id, self._configuration()["retry_limits"]["stage"])
        state = store.initialize()
        if state["current_stage"] == "QUEUED":
            state = store.transition(
                "SOURCE_CHECK",
                "source-check-%s" % clearance["clearance_hash"],
                input_hashes=[dossier["dossier_hash"], *request["packet_hashes"]],
                output_hashes=[clearance["clearance_hash"]],
                policy_hashes=[dossier["rules_hash"]],
            )
        if state["current_stage"] == "SOURCE_CHECK":
            state = store.transition(
                "MANUSCRIPT",
                "manuscript-handoff-%s" % handoff["handoff_hash"],
                input_hashes=locked,
                output_hashes=[handoff["handoff_hash"]],
                policy_hashes=[dossier["rules_hash"]],
            )
        return {
            "status": handoff["status"],
            "book_id": book_id,
            "kind": kind,
            "handoff_hash": handoff["handoff_hash"],
            "request_hash": request["request_hash"],
            "path": str(path),
            "run_stage": state["current_stage"],
            "publication_gate": "BLOCKED",
        }

    def import_manuscript_handoff(self, book_id, handoff_path, response_path):
        _, dossier, packets = self._production_inputs(book_id)
        clearance = self.clearances.latest(book_id)
        validate_private_draft_clearance(clearance, dossier, packets)
        handoff = load_json(Path(handoff_path))
        response = load_json(Path(response_path))
        validate_named(handoff, self.root / "schemas" / "book-factory", "agent-handoff")
        validate_named(response, self.root / "schemas" / "book-factory", "agent-response")
        if handoff.get("book_id") != book_id or handoff.get("kind") not in {"MANUSCRIPT_GENERATION", "MANUSCRIPT_REVISION"}:
            raise ContractError("wrong manuscript handoff")
        if finalize_handoff(handoff) != handoff:
            raise ContractError("manuscript handoff content hash is invalid")
        active_hashes = {
            "dossier_hash": dossier["dossier_hash"],
            "graph_hash": dossier["graph_hash"],
            "rules_hash": dossier["rules_hash"],
            "source_clearance_hash": clearance["clearance_hash"],
        }
        for field, expected in active_hashes.items():
            if handoff["request"].get(field) != expected:
                raise ContractError("manuscript handoff has stale %s" % field)
        if sorted(handoff["request"].get("packet_hashes", [])) != sorted(packet["packet_hash"] for packet in packets):
            raise ContractError("manuscript handoff has stale Story Packet hashes")
        execution = validate_execution(handoff, response, "manuscript_generation")
        manuscript = response.get("result", {}).get("manuscript")
        if not isinstance(manuscript, dict):
            raise ContractError("agent response has no structured manuscript")
        manuscript = dict(manuscript)
        versions = ManuscriptVersionStore(self.books_root).versions(book_id)
        prior = [
            item for item in versions
            if item["payload"].get("creator", {}).get("request_hash") == handoff["request_hash"]
        ]
        if prior:
            record = prior[-1]
            version_label = "v%04d" % record["version"]
            return {
                "status": "MANUSCRIPT_DRAFT_COMPLETE",
                "book_id": book_id,
                "version": record["version"],
                "manuscript_hash": record["content_hash"],
                "structured_path": str(self.books_root / book_id / "manuscripts" / (version_label + ".json")),
                "markdown_path": str(self.books_root / book_id / "manuscripts" / (version_label + ".md")),
                "idempotent_replay": True,
                "publication_gate": "BLOCKED",
            }
        expected_version = len(versions) + 1
        manuscript["version"] = expected_version
        manuscript["book_id"] = book_id
        manuscript["source_packet_hashes"] = sorted(handoff["request"]["packet_hashes"])
        manuscript["source_clearance_hash"] = clearance["clearance_hash"]
        creator = dict(manuscript.get("creator", {}))
        creator.update({
            "id": execution["agent_id"],
            "role": execution.get("role", "manuscript-story"),
            "capability": "manuscript_generation",
            "capability_verified": True,
            "execution_mechanism": execution["mechanism"],
            "request_hash": handoff["request_hash"],
            "attestation_scope": execution["attestation_scope"],
        })
        manuscript["creator"] = creator
        validate_named(manuscript, self.root / "schemas" / "book-factory", "manuscript")
        check = validate_manuscript(
            manuscript,
            handoff["request"]["required_event_ids"],
            allowed_evidence_ids=handoff["request"]["allowed_evidence_ids"],
            expected_packet_hashes=handoff["request"]["packet_hashes"],
            event_evidence_map={
                item["event_id"]: item.get("evidence_ids", [])
                for item in handoff["request"]["event_requirements"]
            },
        )
        if check["result"] != "PASS":
            raise ContractError("manuscript failed deterministic validation", {"findings": check["findings"]})
        parent_hash = versions[-1]["content_hash"] if versions else None
        if handoff["kind"] == "MANUSCRIPT_REVISION" and handoff["request"].get("parent_manuscript_hash") != parent_hash:
            raise ContractError("revision handoff does not bind the latest manuscript parent")
        record = ManuscriptVersionStore(self.books_root).put(book_id, manuscript, parent_hash=parent_hash)
        version_label = "v%04d" % record["version"]
        manuscript_root = self.books_root / book_id / "manuscripts"
        markdown_path = manuscript_root / (version_label + ".md")
        coverage_path = manuscript_root / (version_label + ".event-coverage.json")
        provenance_path = manuscript_root / (version_label + ".claim-provenance.json")
        markdown = render_manuscript_markdown(manuscript).encode("utf-8")
        if markdown_path.exists() and markdown_path.read_bytes() != markdown:
            raise ContractError("immutable manuscript Markdown already differs")
        if not markdown_path.exists():
            atomic_write(markdown_path, markdown)
        coverage_payload = {
            "schema_version": "1.0", "book_id": book_id, "manuscript_hash": record["content_hash"],
            "required_event_ids": handoff["request"]["required_event_ids"], "coverage": manuscript["event_coverage"],
        }
        provenance_payload = {
            "schema_version": "1.0", "book_id": book_id, "manuscript_hash": record["content_hash"],
            "allowed_evidence_ids": handoff["request"]["allowed_evidence_ids"], "claims": manuscript["claim_map"],
        }
        for sidecar_path, payload in ((coverage_path, coverage_payload), (provenance_path, provenance_payload)):
            if sidecar_path.exists() and load_json(sidecar_path) != payload:
                raise ContractError("immutable manuscript sidecar already differs", {"path": str(sidecar_path)})
            if not sidecar_path.exists():
                atomic_json_write(sidecar_path, payload)
        response_record, response_store_path = self.handoffs.store_response(handoff, response)
        state_store = StateStore(self.books_root, book_id, self._configuration()["retry_limits"]["stage"])
        state = state_store.load()
        if state["current_stage"] == "MANUSCRIPT":
            state = state_store.transition(
                "EDITORIAL_QA",
                "import-manuscript-%s" % record["content_hash"],
                actor=execution["agent_id"],
                input_hashes=handoff["locked_input_hashes"],
                output_hashes=[record["content_hash"], response_record["response_hash"]],
                policy_hashes=[dossier["rules_hash"]],
            )
        awaiting_review_status = {
            "schema_version": "1.0",
            "book_id": book_id,
            "source_readiness": dossier["status"],
            "private_draft_gate": clearance["private_draft_gate"],
            "manuscript_draft_completion": "COMPLETE",
            "independent_editorial_review": "AWAITING_REVIEW",
            "visual_production": "NOT_STARTED_PR4_BOUNDARY",
            "publication_readiness": "BLOCKED",
            "latest_manuscript_hash": record["content_hash"],
            "revision_required": False,
            "exact_result": (
                "PRIVATE_MANUSCRIPT_REVISION_COMPLETE_AWAITING_INDEPENDENT_REREVIEW_PUBLICATION_BLOCKED"
                if record["version"] > 1
                else "PRIVATE_MANUSCRIPT_COMPLETE_AWAITING_INDEPENDENT_REVIEW_PUBLICATION_BLOCKED"
            ),
        }
        awaiting_review_status["status_hash"] = content_hash(awaiting_review_status)
        atomic_json_write(self.books_root / book_id / "production-status.json", awaiting_review_status)
        return {
            "status": "MANUSCRIPT_DRAFT_COMPLETE",
            "book_id": book_id,
            "version": record["version"],
            "manuscript_hash": record["content_hash"],
            "structured_path": str(manuscript_root / (version_label + ".json")),
            "markdown_path": str(markdown_path),
            "coverage_path": str(coverage_path),
            "provenance_path": str(provenance_path),
            "response_path": str(response_store_path),
            "deterministic_check": check,
            "next_stage": "EDITORIAL_QA",
            "publication_gate": "BLOCKED",
        }

    def prepare_review_handoff(self, book_id):
        _, dossier, packets = self._production_inputs(book_id)
        clearance = self.clearances.latest(book_id)
        validate_private_draft_clearance(clearance, dossier, packets)
        manuscripts = ManuscriptVersionStore(self.books_root).versions(book_id)
        if not manuscripts:
            raise ContractError("no immutable manuscript exists to review")
        manuscript = manuscripts[-1]
        required_events = [event["id"] for packet in packets for event in packet.get("events", [])]
        packet_hashes = [packet["packet_hash"] for packet in packets]
        request = build_review_request(
            manuscript,
            packet_hashes,
            required_events,
            dossier["dossier_hash"],
            clearance["clearance_hash"],
            packets=packets,
        )
        handoff, path = self.handoffs.prepare(
            book_id,
            "EDITORIAL_REVIEW",
            request,
            "family-editor",
            [manuscript["content_hash"], dossier["dossier_hash"], clearance["clearance_hash"], *packet_hashes],
            writer_id=request["writer_id"],
        )
        return {
            "status": handoff["status"],
            "book_id": book_id,
            "handoff_hash": handoff["handoff_hash"],
            "request_hash": request["request_hash"],
            "path": str(path),
            "writer_id": request["writer_id"],
            "required_independence": True,
        }

    def import_review_handoff(self, book_id, handoff_path, response_path):
        _, dossier, packets = self._production_inputs(book_id)
        clearance = self.clearances.latest(book_id)
        validate_private_draft_clearance(clearance, dossier, packets)
        handoff = load_json(Path(handoff_path))
        response = load_json(Path(response_path))
        validate_named(handoff, self.root / "schemas" / "book-factory", "agent-handoff")
        validate_named(response, self.root / "schemas" / "book-factory", "agent-response")
        if handoff.get("book_id") != book_id or handoff.get("kind") != "EDITORIAL_REVIEW":
            raise ContractError("wrong editorial-review handoff")
        if finalize_handoff(handoff) != handoff:
            raise ContractError("editorial-review handoff content hash is invalid")
        if handoff["request"].get("dossier_hash") != dossier["dossier_hash"]:
            raise ContractError("editorial-review handoff has a stale dossier hash")
        if handoff["request"].get("source_clearance_hash") != clearance["clearance_hash"]:
            raise ContractError("editorial-review handoff has a stale clearance hash")
        if sorted(handoff["request"].get("reviewed_packet_hashes", [])) != sorted(packet["packet_hash"] for packet in packets):
            raise ContractError("editorial-review handoff has stale Story Packet hashes")
        execution = validate_execution(
            handoff, response, "editorial_review", writer_id=handoff.get("required_independence_from_writer_id")
        )
        review_input = response.get("result", {}).get("review")
        if not isinstance(review_input, dict):
            raise ContractError("agent response has no structured editorial review")
        reviewer = dict(review_input)
        reviewer.update({
            "id": execution["agent_id"],
            "independent": True,
            "capability_verified": True,
            "provider_kind": "editorial_review",
        })
        manuscripts = ManuscriptVersionStore(self.books_root).versions(book_id)
        current = manuscripts[-1]
        if handoff["request"].get("reviewed_manuscript_hash") != current["content_hash"]:
            raise ContractError("editorial-review handoff does not bind the latest manuscript")
        allowed_evidence = sorted({citation["id"] for packet in packets for citation in packet.get("citations", [])})
        gate = editorial_review(
            current["payload"],
            handoff["request"]["required_event_ids"],
            reviewer,
            manuscript_hash=current["content_hash"],
            packet_hashes=handoff["request"]["reviewed_packet_hashes"],
            allowed_evidence_ids=allowed_evidence,
            event_evidence_map={
                event["id"]: event.get("evidence_ids", [])
                for packet in packets for event in packet.get("events", [])
            },
        )
        finalized = finalize_review(book_id, review_input, gate, execution)
        validate_named(finalized, self.root / "schemas" / "book-factory", "editorial-review")
        prior_reviews = EditorialReviewStore(self.books_root).versions(book_id)
        matching_reviews = [
            item for item in prior_reviews
            if item["payload"].get("review_hash") == finalized["review_hash"]
        ]
        if matching_reviews:
            record = matching_reviews[-1]
            status_path = self.books_root / book_id / "production-status.json"
            return {
                "status": load_json(status_path)["exact_result"] if status_path.exists() else "EDITORIAL_REVIEW_COMPLETE",
                "book_id": book_id,
                "review_result": finalized["result"],
                "review_hash": finalized["review_hash"],
                "review_version_hash": record["content_hash"],
                "idempotent_replay": True,
                "publication_gate": "BLOCKED",
            }
        parent_hash = prior_reviews[-1]["content_hash"] if prior_reviews else None
        record = EditorialReviewStore(self.books_root).put(book_id, finalized, parent_hash=parent_hash)
        response_record, stored_response_path = self.handoffs.store_response(handoff, response)
        revision = None
        if finalized["result"] == "FIX":
            revision = targeted_revision_request(finalized)
            validate_named(revision, self.root / "schemas" / "book-factory", "revision-request")
            revision_path = self.books_root / book_id / "revisions" / (revision["request_hash"] + ".json")
            atomic_json_write(revision_path, revision)
        status = {
            "schema_version": "1.0",
            "book_id": book_id,
            "source_readiness": dossier["status"],
            "private_draft_gate": clearance["private_draft_gate"],
            "manuscript_draft_completion": "COMPLETE",
            "independent_editorial_review": finalized["result"],
            "visual_production": "NOT_STARTED_PR4_BOUNDARY",
            "publication_readiness": "BLOCKED",
            "publication_blockers": [
                "WORLDWIDE_OR_TARGET_MARKET_PUBLICATION_RIGHTS_NOT_CLEARED",
                "CHAPTER_EXTRACTION_ATOMICALLY_PARTIAL",
                "INDEPENDENT_FULL_ARC_SOURCE_APPROVAL_NOT_ESTABLISHED",
                "VISUAL_PRODUCTION_NOT_STARTED",
            ],
            "latest_manuscript_hash": current["content_hash"],
            "latest_review_hash": finalized["review_hash"],
            "revision_required": finalized["result"] == "FIX",
            "exact_result": (
                "PRIVATE_MANUSCRIPT_REQUIRES_REVISION_PUBLICATION_BLOCKED"
                if finalized["result"] == "FIX"
                else "PRIVATE_MANUSCRIPT_EDITORIALLY_REVIEWED_PUBLICATION_BLOCKED"
                if finalized["result"] == "PASS"
                else "PRIVATE_MANUSCRIPT_ESCALATED_PUBLICATION_BLOCKED"
            ),
        }
        status["status_hash"] = content_hash(status)
        atomic_json_write(self.books_root / book_id / "production-status.json", status)
        return {
            "status": status["exact_result"],
            "book_id": book_id,
            "review_result": finalized["result"],
            "review_hash": finalized["review_hash"],
            "review_version_hash": record["content_hash"],
            "review_path": str(self.books_root / book_id / "editorial-reviews" / ("v%04d.json" % record["version"])),
            "response_path": str(stored_response_path),
            "revision_request": revision,
            "production_status": status,
        }

    def manuscript_status(self, book_id):
        manifests = ManuscriptVersionStore(self.books_root).versions(book_id)
        reviews = EditorialReviewStore(self.books_root).versions(book_id)
        path = self.books_root / book_id / "production-status.json"
        return {
            "book_id": book_id,
            "manuscript_versions": len(manifests),
            "review_versions": len(reviews),
            "latest_manuscript_hash": manifests[-1]["content_hash"] if manifests else None,
            "latest_review_hash": reviews[-1]["payload"].get("review_hash") if reviews else None,
            "production_status": load_json(path) if path.exists() else "NOT_RECORDED",
        }

    def draft_manuscript(self, book_id, dry_run=False):
        manifest, dossier, packets = self._production_inputs(book_id)
        clearance = self.clearances.latest(book_id)
        validate_private_draft_clearance(clearance, dossier, packets)
        request = build_manuscript_request(
            manifest, dossier, packets, dossier["rules_hash"], clearance=clearance
        )
        validate_named(request, self.root / "schemas" / "book-factory", "manuscript-request")
        capability = self.providers.capabilities()["manuscript_generation"]
        if not capability["available"]:
            return {
                "status": "BLOCKED_PROVIDER",
                "book_id": book_id,
                "provider": capability,
                "request": request,
                "dry_run": bool(dry_run),
                "mutated": False,
                "manuscript_created": False,
            }
        if dry_run:
            return {"status": "DRY_RUN", "book_id": book_id, "request": request, "mutated": False}
        raise NotImplementedStageError("an approved manuscript provider adapter is required before execution")

    def review_manuscript(self, book_id):
        capability = self.providers.capabilities()["editorial_review"]
        if not capability["available"]:
            return {
                "status": "BLOCKED_REVIEWER",
                "book_id": book_id,
                "provider": capability,
                "mutated": False,
                "review_created": False,
            }
        raise NotImplementedStageError("an approved independent editorial-review adapter is required before execution")

    def produce_next(self, dry_run=False):
        if not dry_run:
            raise NotImplementedStageError("Foundation PR3 supports produce-next only with --dry-run")
        active_ids = {
            path.parents[1].name
            for path in self.books_root.glob("*/run/state.json")
            if StateStore(self.books_root, path.parents[1].name).load()["current_stage"] not in {"READY_FOR_PUBLICATION", "BLOCKED", "FAILED"}
        }
        candidates = [
            item for item in self.catalogue.list_books()
            if item["id"] not in active_ids
            and item.get("edition_status") != "EXISTING_EDITION"
            and item.get("automatic_production_eligible", True)
            and item.get("readiness") == "READY"
        ]
        candidates.sort(key=lambda item: (item.get("priority", 1000), item["id"]))
        selected = None
        for candidate in candidates:
            dossier = self.source_intelligence.assess(candidate, self.mappings.resolve(candidate["id"]))
            if dossier["status"] == "READY":
                selected = candidate
                break
        standards = rules_status(self.root)
        if selected is None:
            return {
                "status": "NO_READY_BOOKS",
                "selected_book": None,
                "standards": standards,
                "mutated": False,
            }
        if standards["status"] != "AVAILABLE":
            return {
                "status": "BLOCKED_STANDARD",
                "selected_book": selected["id"],
                "standards": standards,
                "mutated": False,
            }
        return {
            "status": "DRY_RUN",
            "selected_book": selected["id"],
            "next_stage": "SOURCE_CHECK",
            "mutated": False,
        }

    def resume(self, book_id):
        book = self.catalogue.get(book_id)
        if book is None:
            return {
                "status": "BLOCKED",
                "code": "BOOK_NOT_FOUND",
                "book_id": book_id,
                "message": "import the authoritative catalogue entry before resuming",
                "mutated": False,
            }
        store = StateStore(self.books_root, book_id, self._configuration()["retry_limits"]["stage"])
        if not store.events_path.exists():
            return {
                "status": "BLOCKED",
                "code": "STATE_NOT_INITIALIZED",
                "book_id": book_id,
                "message": "this book has no durable run state",
                "mutated": False,
            }
        state = store.load()
        if state["current_stage"] == "MANUSCRIPT":
            requests = sorted((self.books_root / book_id / "handoffs" / "manuscript-generation").glob("*.request.json"))
            if requests:
                handoff = load_json(requests[-1])
                if finalize_handoff(handoff) != handoff:
                    raise ContractError("stored manuscript handoff failed hash revalidation")
                return {
                    "status": "AWAITING_CODEX_SPECIALIST_AGENT",
                    "book_id": book_id,
                    "current_stage": "MANUSCRIPT",
                    "handoff_hash": handoff["handoff_hash"],
                    "request_path": str(requests[-1]),
                    "message": "resume from the existing locked handoff; source work was not repeated",
                    "mutated": False,
                }
        if state["current_stage"] == "EDITORIAL_QA":
            revision_requests = sorted((self.books_root / book_id / "handoffs" / "manuscript-revision").glob("*.request.json"))
            if revision_requests:
                revision_handoff = load_json(revision_requests[-1])
                imported_request_hashes = {
                    item["payload"].get("creator", {}).get("request_hash")
                    for item in ManuscriptVersionStore(self.books_root).versions(book_id)
                }
                if revision_handoff["request_hash"] not in imported_request_hashes:
                    return {
                        "status": "AWAITING_CODEX_REVISION_AGENT",
                        "book_id": book_id,
                        "current_stage": "EDITORIAL_QA",
                        "handoff_hash": revision_handoff["handoff_hash"],
                        "request_path": str(revision_requests[-1]),
                        "message": "resume from the bounded revision handoff; the rejected manuscript remains immutable",
                        "mutated": False,
                    }
            status_path = self.books_root / book_id / "production-status.json"
            if status_path.exists():
                status = load_json(status_path)
                return {
                    "status": status["exact_result"],
                    "book_id": book_id,
                    "current_stage": "EDITORIAL_QA",
                    "production_status": status,
                    "mutated": False,
                }
            requests = sorted((self.books_root / book_id / "handoffs" / "editorial-review").glob("*.request.json"))
            if requests:
                handoff = load_json(requests[-1])
                if finalize_handoff(handoff) != handoff:
                    raise ContractError("stored editorial handoff failed hash revalidation")
                return {
                    "status": "AWAITING_INDEPENDENT_EDITOR",
                    "book_id": book_id,
                    "current_stage": "EDITORIAL_QA",
                    "handoff_hash": handoff["handoff_hash"],
                    "request_path": str(requests[-1]),
                    "message": "resume from the existing locked review handoff; the manuscript was not regenerated",
                    "mutated": False,
                }
        target = state.get("recovery", {}).get("resume_stage") if state["current_stage"] in {"BLOCKED", "FAILED"} else next_stage(state["current_stage"])
        required_provider = {"MANUSCRIPT": "manuscript_generation", "EDITORIAL_QA": "editorial_review"}.get(target)
        if required_provider:
            capability = self.providers.capabilities()[required_provider]
            if not capability["available"]:
                return {
                    "status": "BLOCKED_PROVIDER" if target == "MANUSCRIPT" else "BLOCKED_REVIEWER",
                    "book_id": book_id,
                    "current_stage": state["current_stage"],
                    "requested_stage": target,
                    "provider": capability,
                    "message": "capability remains unavailable; durable state and completed source work are unchanged",
                    "mutated": False,
                }
        return {
            "status": "NOT_IMPLEMENTED",
            "book_id": book_id,
            "current_stage": state["current_stage"],
            "requested_stage": target,
            "message": "Foundation PR3 does not execute production stages",
            "mutated": False,
        }

    def validate(self):
        self._configuration()
        catalogue = self.catalogue.load()
        schema_root = self.root / "schemas" / "book-factory"
        validate_named(catalogue, schema_root, "catalogue")
        if catalogue.get("metadata", {}).get("normalization") == "LOSSLESS_V01_WITH_NAMESPACED_FACTORY_DERIVATIONS":
            raw_catalogue_path = self.root / "book-factory" / "inputs" / "catalogues" / "Khatakshetra_Illustrated_Library_Catalogue_v0.1.json"
            raw_catalogue_hash = sha256_bytes(raw_catalogue_path.read_bytes())
            if raw_catalogue_hash != catalogue["metadata"]["source_sha256"]:
                raise ContractError("normalized catalogue does not match its immutable source", {"actual": raw_catalogue_hash})
        schemas = []
        for path in sorted(schema_root.glob("*.schema.json")):
            name = path.name.replace(".schema.json", "")
            schema = load_schema(path.parent, name)
            if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
                raise ContractError("%s is not a draft 2020-12 schema" % path.name)
            schemas.append(path.name)
        worker_contracts = []
        for path in sorted((self.root / "book-factory" / "contracts" / "workers").glob("*.json")):
            validate_named(load_json(path), schema_root, "worker-contract")
            worker_contracts.append(path.name)
        validate_named(load_json(self.root / "book-factory" / "policies" / "spending-policy.json"), schema_root, "budget")
        fixture = load_json(self.root / "book-factory" / "fixtures" / "synthetic-book" / "catalogue.json")
        validate_named(fixture, schema_root, "catalogue")
        graph_report = self.graph.verify()
        mapping_validation = PilotSelector(self.graph, self.mappings).validate_mappings(catalogue["books"])
        reference_registry = load_json(self.root / "book-factory" / "references" / "reference-assets.json")
        reference_assets = []
        for item in reference_registry["assets"]:
            path = self.root / item["path"]
            if not path.is_file():
                reference_assets.append({
                    "path": item["path"],
                    "sha256": item["sha256"],
                    "availability": "MISSING_LOCAL_REFERENCE",
                })
                continue
            digest = sha256_bytes(path.read_bytes())
            if digest != item["sha256"] or path.stat().st_size != item["bytes"]:
                raise ContractError("reference asset hash mismatch", {"path": item["path"], "actual": digest})
            reference_assets.append({
                "path": item["path"],
                "sha256": digest,
                "availability": "AVAILABLE_LOCAL_REFERENCE",
            })
        dm08 = self.reference_editions.verify("DM08")
        source_clearances = []
        for path in sorted(self.books_root.glob("*/source-clearance/*.json")):
            record = load_json(path)
            validate_named(record, schema_root, "source-clearance")
            finalized = finalize_clearance(record)
            if finalized != record:
                raise ContractError("source clearance content hash is invalid", {"path": str(path)})
            source_clearances.append({"book_id": record["book_id"], "clearance_hash": record["clearance_hash"]})
        agent_handoffs = []
        for path in sorted(self.books_root.glob("*/handoffs/**/*.request.json")):
            record = load_json(path)
            validate_named(record, schema_root, "agent-handoff")
            if finalize_handoff(record) != record:
                raise ContractError("agent handoff content hash is invalid", {"path": str(path)})
            agent_handoffs.append({"book_id": record["book_id"], "kind": record["kind"], "handoff_hash": record["handoff_hash"]})
        agent_responses = []
        for path in sorted(self.books_root.glob("*/handoffs/**/*.response.json")):
            record = load_json(path)
            validate_named(record, schema_root, "agent-response")
            unsigned_response = {
                key: value for key, value in record.items()
                if key not in {"response_hash", "id", "stored_at"}
            }
            if record.get("response_hash") != content_hash(unsigned_response):
                raise ContractError("agent response content hash is invalid", {"path": str(path)})
            agent_responses.append({
                "agent_id": record["execution"].get("agent_id"),
                "capability": record["execution"].get("capability"),
                "response_hash": record.get("response_hash"),
            })
        manuscript_versions = []
        editorial_review_versions = []
        for book_root in sorted(path for path in self.books_root.iterdir() if path.is_dir() and path.name != "_artifacts"):
            for record in ManuscriptVersionStore(self.books_root).versions(book_root.name):
                validate_named(record["payload"], schema_root, "manuscript")
                manuscript_versions.append({"book_id": book_root.name, "content_hash": record["content_hash"]})
            for record in EditorialReviewStore(self.books_root).versions(book_root.name):
                validate_named(record["payload"], schema_root, "editorial-review")
                editorial_review_versions.append({"book_id": book_root.name, "content_hash": record["content_hash"]})
        return {
            "status": "PASS",
            "schemas": schemas,
            "worker_contracts": worker_contracts,
            "source_graph": {"passed": graph_report["passed"], "graph_hash": graph_report["graph_hash"]},
            "rules": rules_status(self.root),
            "reference_assets": reference_assets,
            "reference_editions": [dm08],
            "source_clearances": source_clearances,
            "agent_handoffs": agent_handoffs,
            "agent_responses": agent_responses,
            "manuscript_versions": manuscript_versions,
            "editorial_review_versions": editorial_review_versions,
            "catalogue_mapping_validation": mapping_validation,
            "input_report": self.input_report(),
            "note": "Foundation PR4 supports audited Codex session handoffs for manuscripts and independent review; illustration and PDF production remain out of scope",
        }
