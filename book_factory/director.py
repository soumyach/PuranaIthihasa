"""Single user-facing orchestration facade for the Khatakshetra Book Factory."""

import json
from copy import deepcopy
from pathlib import Path

from . import __version__
from .artifacts import ArtifactStore
from .catalogue import CatalogueStore
from .catalogue_v01 import SourceMappingRegistry
from .contracts import load_schema, validate_named
from .drafting import (
    build_manuscript_request,
    build_review_request,
    pr5_quality_revision_request,
    render_manuscript_markdown,
    targeted_revision_request,
)
from .editorial import PR5_REVIEW_PERSPECTIVES, editorial_review, finalize_review
from .errors import ContractError, NotImplementedStageError
from .handoffs import SessionHandoffStore, finalize_handoff, validate_execution
from .illustration_production import (
    ProofExecutionLedger,
    build_character_reference_registry,
    build_contact_sheet_svg,
    build_generation_request,
    build_style_approval_request,
    discover_image_backends,
    finalize_visual_review,
    store_snapshot,
    validate_proof_receipts,
    visual_review_request,
)
from .narrative import validate_manuscript
from .orchestration import AutonomousFactoryDirector
from .pilot import PilotSelector, catalogue_readiness_report
from .page_engine import (
    FontResolver,
    compose_book as render_book,
    compose_page as render_page,
    export_pdf as build_reader_pdf,
    inspect_pdf as inspect_reader_pdf,
    validate_composition_file,
)
from .preproduction import build_semantic_visual_review_request, validate_preproduction_package
from .production_integration import RealProductionSlice
from .providers import CodexNativeImageProvider
from .providers.base import ProviderRegistry
from .references import ReferenceEditionRegistry
from .rules import rules_status
from .source_graph import ReadOnlySourceGraph
from .source_intelligence import DossierStore, SourceReadinessAssessor, StoryPacketBuilder, StoryPacketStore
from .source_clearance import SourceClearanceStore, finalize_clearance, validate_private_draft_clearance
from .state import StateStore, next_stage
from .util import atomic_json_write, atomic_write, content_hash, load_json, sha256_bytes
from .visual_benchmark import prepare_recovery_requests, validate_gold_standard, validate_pr7
from .versioning import (
    CharacterBibleVersionStore,
    CharacterReferenceVersionStore,
    EditorialReviewStore,
    IllustrationProofVersionStore,
    LocationBibleVersionStore,
    ManuscriptVersionStore,
    PreproductionReviewVersionStore,
    ProofRecoveryRequestVersionStore,
    ProofSpecVersionStore,
    StoryboardVersionStore,
    StyleApprovalRequestVersionStore,
    TypographyVersionStore,
    VisualReviewVersionStore,
    PageCompositionVersionStore,
    PdfArtifactVersionStore,
)


class FactoryDirector:
    def __init__(self, repository_root, catalogue_path=None, orchestration_runtime_root=None):
        self.root = Path(repository_root).resolve()
        self.books_root = self.root / "books"
        self.catalogue = CatalogueStore(Path(catalogue_path).resolve() if catalogue_path else self.books_root / "catalogue.json")
        self.graph = ReadOnlySourceGraph(self.root / "research" / "source-graph")
        self.source_intelligence = SourceReadinessAssessor(self.graph, self.root)
        self.providers = ProviderRegistry({"image": CodexNativeImageProvider()})
        self.mappings = SourceMappingRegistry(self.root / "book-factory" / "config" / "catalogue-source-mappings.json")
        self.reference_editions = ReferenceEditionRegistry(self.root)
        self.clearances = SourceClearanceStore(self.books_root)
        self.handoffs = SessionHandoffStore(self.books_root)
        self.real_production = RealProductionSlice(self.root)
        self.orchestrator = AutonomousFactoryDirector(self, orchestration_runtime_root)

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
            "implementation": "CONTROLLED_VISUAL_PRODUCTION_PILOT_PR11",
            "catalogue_books": len(books),
            "readiness_counts": {state: sum(book["readiness"] == state for book in books) for state in sorted({book["readiness"] for book in books})},
            "active_runs": states,
            "rules": rules_status(self.root),
            "providers": self.providers.capabilities(),
            "image_generation_environment": self.image_capabilities(),
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
            "visual_gold_standard": validate_gold_standard(self.root),
            "proof_recovery": "PREPARED_NOT_AUTHORIZED_NOT_EXECUTED",
            "page_engine": {
                "version": __version__,
                "production_stage_gates": ["LETTERING", "PDF_LAYOUT", "VISUAL_QA"],
                "fixture_mode": "ISOLATED_PUBLICATION_INELIGIBLE",
                "semantic_visual_approval": "REQUIRES_INDEPENDENT_ACTUAL_PIXEL_REVIEW",
            },
            "autonomous_orchestration": self.orchestrator.status(),
            "real_production_slice": (
                self.real_production.status()
                if (self.books_root / "DM04" / "production-slices" / "v0001.json").is_file()
                else {"status": "NOT_PREPARED"}
            ),
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

    def prepare_manuscript_handoff(self, book_id, revision_review_hash=None, pr5_quality_revision=False):
        manifest, dossier, packets = self._production_inputs(book_id)
        clearance = self.clearances.latest(book_id)
        validate_private_draft_clearance(clearance, dossier, packets)
        versions = ManuscriptVersionStore(self.books_root).versions(book_id)
        parent = versions[-1] if versions else None
        revision = None
        kind = "MANUSCRIPT_GENERATION"
        milestone_contract = None
        if pr5_quality_revision:
            if revision_review_hash:
                raise ContractError("PR5 quality revision and FIX-review revision are mutually exclusive")
            if not parent or parent["version"] != 2:
                raise ContractError("PR5 quality revision requires immutable DM04 manuscript v2 as latest parent")
            reviews = EditorialReviewStore(self.books_root).versions(book_id)
            passed = [
                item for item in reviews
                if item["payload"].get("result") == "PASS"
                and item["payload"].get("reviewed_manuscript_hash") == parent["content_hash"]
            ]
            if not passed:
                raise ContractError("PR5 quality revision requires the independent PASS review bound to v2")
            revision = pr5_quality_revision_request(parent, passed[-1])
            milestone_contract = revision
            kind = "MANUSCRIPT_REVISION"
        elif revision_review_hash:
            reviews = EditorialReviewStore(self.books_root).versions(book_id)
            matching = [item for item in reviews if item["payload"].get("review_hash") == revision_review_hash]
            if not matching:
                raise ContractError("revision review hash is not an immutable review version")
            if matching[-1]["payload"].get("result") != "FIX":
                raise ContractError("only a FIX review can authorize manuscript revision")
            if matching[-1]["payload"].get("reviewed_manuscript_hash") != parent["content_hash"]:
                raise ContractError("a FIX review can revise only the exact latest manuscript it reviewed")
            fix_review_count = len({
                item["payload"].get("review_hash") for item in reviews
                if item["payload"].get("result") == "FIX"
            })
            if fix_review_count > self._configuration()["retry_limits"]["qa_repair"]:
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
            milestone_contract=milestone_contract,
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
            "required_review_perspectives": (
                sorted(PR5_REVIEW_PERSPECTIVES) if record["version"] >= 3 else ["LEGACY_COMBINED"]
            ),
            "completed_review_perspectives": [],
            "visual_production": "NOT_STARTED",
            "publication_readiness": "BLOCKED",
            "latest_manuscript_hash": record["content_hash"],
            "revision_required": False,
            "exact_result": (
                "MANUSCRIPT_PR5_TARGETED_REVISION_COMPLETE_AWAITING_DUAL_INDEPENDENT_REVIEW_PUBLICATION_BLOCKED"
                if record["version"] > 3 else
                "MANUSCRIPT_V3_COMPLETE_AWAITING_DUAL_INDEPENDENT_REVIEW_PUBLICATION_BLOCKED"
                if record["version"] == 3 else
                "PRIVATE_MANUSCRIPT_REVISION_COMPLETE_AWAITING_INDEPENDENT_REREVIEW_PUBLICATION_BLOCKED"
                if record["version"] > 1 else
                "PRIVATE_MANUSCRIPT_COMPLETE_AWAITING_INDEPENDENT_REVIEW_PUBLICATION_BLOCKED"
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

    def prepare_review_handoff(self, book_id, perspective=None):
        _, dossier, packets = self._production_inputs(book_id)
        clearance = self.clearances.latest(book_id)
        validate_private_draft_clearance(clearance, dossier, packets)
        manuscripts = ManuscriptVersionStore(self.books_root).versions(book_id)
        if not manuscripts:
            raise ContractError("no immutable manuscript exists to review")
        manuscript = manuscripts[-1]
        if manuscript["version"] >= 3:
            if perspective not in PR5_REVIEW_PERSPECTIVES:
                raise ContractError("PR5 review requires SOURCE_FIDELITY or LITERARY_EXPERIENCE perspective")
        else:
            perspective = perspective or "LEGACY_COMBINED"
            if perspective != "LEGACY_COMBINED":
                raise ContractError("pre-PR5 manuscripts use the legacy combined review contract")
        prior_reviews = EditorialReviewStore(self.books_root).versions(book_id)
        if any(
            item["payload"].get("reviewed_manuscript_hash") == manuscript["content_hash"]
            and item["payload"].get("review_perspective", "LEGACY_COMBINED") == perspective
            for item in prior_reviews
        ):
            raise ContractError("this manuscript and review perspective already have an immutable review")
        required_events = [event["id"] for packet in packets for event in packet.get("events", [])]
        packet_hashes = [packet["packet_hash"] for packet in packets]
        request = build_review_request(
            manuscript,
            packet_hashes,
            required_events,
            dossier["dossier_hash"],
            clearance["clearance_hash"],
            packets=packets,
            perspective=perspective,
        )
        role = "source-evidence" if perspective == "SOURCE_FIDELITY" else "family-editor"
        handoff, path = self.handoffs.prepare(
            book_id,
            "EDITORIAL_REVIEW",
            request,
            role,
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
            "review_perspective": perspective,
            "required_dimensions": request["required_dimensions"],
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
        perspective = handoff["request"].get("review_perspective", "LEGACY_COMBINED")
        if review_input.get("review_perspective", "LEGACY_COMBINED") != perspective:
            raise ContractError("editorial response perspective does not match the locked request")
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
            required_dimensions=set(handoff["request"]["required_dimensions"]),
            require_event_checks=handoff["request"].get("require_source_event_checks", True),
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
        current_reviews = [*prior_reviews, record]
        perspective_results = {
            item["payload"].get("review_perspective", "LEGACY_COMBINED"): item["payload"].get("result")
            for item in current_reviews
            if item["payload"].get("reviewed_manuscript_hash") == current["content_hash"]
        }
        pr5_dual_pass = all(perspective_results.get(name) == "PASS" for name in PR5_REVIEW_PERSPECTIVES)
        any_fix = any(value == "FIX" for value in perspective_results.values())
        any_escalate = any(value == "ESCALATE" for value in perspective_results.values())
        if current["version"] >= 3:
            pr5_label = "MANUSCRIPT_V3" if current["version"] == 3 else "MANUSCRIPT_PR5_LATEST_REVISION"
            exact_result = (
                "%s_REQUIRES_REVISION_PUBLICATION_BLOCKED" % pr5_label if any_fix else
                "%s_REVIEW_ESCALATED_PUBLICATION_BLOCKED" % pr5_label if any_escalate else
                "%s_DUAL_REVIEWED_VISUAL_PREPRODUCTION_PENDING_PUBLICATION_BLOCKED" % pr5_label if pr5_dual_pass else
                "%s_AWAITING_SECOND_INDEPENDENT_REVIEW_PUBLICATION_BLOCKED" % pr5_label
            )
            editorial_summary = "PASS" if pr5_dual_pass else "FIX" if any_fix else "ESCALATE" if any_escalate else "PARTIAL_PASS"
        else:
            exact_result = (
                "PRIVATE_MANUSCRIPT_REQUIRES_REVISION_PUBLICATION_BLOCKED"
                if finalized["result"] == "FIX"
                else "PRIVATE_MANUSCRIPT_EDITORIALLY_REVIEWED_PUBLICATION_BLOCKED"
                if finalized["result"] == "PASS"
                else "PRIVATE_MANUSCRIPT_ESCALATED_PUBLICATION_BLOCKED"
            )
            editorial_summary = finalized["result"]
        status = {
            "schema_version": "1.0",
            "book_id": book_id,
            "source_readiness": dossier["status"],
            "private_draft_gate": clearance["private_draft_gate"],
            "manuscript_draft_completion": "COMPLETE",
            "independent_editorial_review": editorial_summary,
            "required_review_perspectives": (
                sorted(PR5_REVIEW_PERSPECTIVES) if current["version"] >= 3 else ["LEGACY_COMBINED"]
            ),
            "completed_review_perspectives": sorted(perspective_results),
            "review_results_by_perspective": perspective_results,
            "visual_production": "NOT_STARTED",
            "publication_readiness": "BLOCKED",
            "publication_blockers": [
                "WORLDWIDE_OR_TARGET_MARKET_PUBLICATION_RIGHTS_NOT_CLEARED",
                "CHAPTER_EXTRACTION_ATOMICALLY_PARTIAL",
                "INDEPENDENT_FULL_ARC_SOURCE_APPROVAL_NOT_ESTABLISHED",
                "VISUAL_PRODUCTION_NOT_STARTED",
            ],
            "latest_manuscript_hash": current["content_hash"],
            "latest_review_hash": finalized["review_hash"],
            "revision_required": any_fix if current["version"] >= 3 else finalized["result"] == "FIX",
            "exact_result": exact_result,
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

    def _pr5_review_gate(self, book_id):
        manuscripts = ManuscriptVersionStore(self.books_root).versions(book_id)
        if not manuscripts or manuscripts[-1]["version"] < 3:
            raise ContractError("visual preproduction requires immutable manuscript v3")
        current = manuscripts[-1]
        reviews = EditorialReviewStore(self.books_root).versions(book_id)
        results = {
            item["payload"].get("review_perspective"): item["payload"].get("result")
            for item in reviews
            if item["payload"].get("reviewed_manuscript_hash") == current["content_hash"]
        }
        missing = sorted(name for name in PR5_REVIEW_PERSPECTIVES if results.get(name) != "PASS")
        if missing:
            raise ContractError("visual preproduction requires both PR5 independent PASS reviews", {"missing": missing})
        return current, reviews

    def prepare_preproduction_handoff(self, book_id):
        _, dossier, packets = self._production_inputs(book_id)
        current, reviews = self._pr5_review_gate(book_id)
        review_hashes = [
            item["payload"]["review_hash"] for item in reviews
            if item["payload"].get("reviewed_manuscript_hash") == current["content_hash"]
            and item["payload"].get("review_perspective") in PR5_REVIEW_PERSPECTIVES
        ]
        request = {
            "schema_version": "1.0",
            "book_id": book_id,
            "milestone": "PR5_VISUAL_PREPRODUCTION",
            "manuscript_hash": current["content_hash"],
            "manuscript": current["payload"],
            "packet_hashes": sorted(packet["packet_hash"] for packet in packets),
            "review_hashes": sorted(review_hashes),
            "required_event_ids": [event["id"] for packet in packets for event in packet.get("events", [])],
            "locked_source_evidence": [
                {
                    "packet_hash": packet["packet_hash"],
                    "events": packet.get("events", []),
                    "citations": packet.get("citations", []),
                    "characters": packet.get("characters", []),
                    "manifestations_boons_powers": packet.get("manifestations_boons_powers", []),
                    "variants_and_conflicts": packet.get("variants_and_conflicts", []),
                    "adaptation_boundaries": packet.get("adaptation_boundaries", []),
                }
                for packet in packets
            ],
            "frame_evidence_boundary": {
                "permitted_for_context_only": ["dm-evidence-001", "dm-evidence-002", "dm-evidence-003"],
                "rule": "Suratha, Samadhi and Medhas may support the frame, but new listener reactions remain explicitly labelled literary adaptation.",
                "source_graph_mutation_allowed": False,
            },
            "required_character_groups": [
                "Devi", "Mahishasura and each sourced form", "Devi's lion", "principal gods",
                "principal commanders", "Medhas", "Suratha", "Samadhi",
            ],
            "required_locations": [
                "forest hermitage", "gods' gathering", "manifestation space", "battlefield",
                "Mahishasura arrival", "thanksgiving",
            ],
            "canvas": {"aspect_ratio": "3:4", "pixel_width": 1086, "pixel_height": 1448},
            "palette": ["#071F35", "#D8AC4E", "#F0CF76", "#F6E8C6", "#FFF9EF", "#251C18", "#692019"],
            "text_channels": ["NARRATION", "DIALOGUE", "THOUGHT", "INSET_EXPLANATION"],
            "proof_kinds": ["QUIET_CONVERSATION", "DIVINE_REVEAL", "BATTLE", "FULL_PAGE_IMMERSION"],
            "proof_retry_limit": 2,
            "constraints": [
                "Return structured bibles, a complete page-by-page storyboard, typography spec and four proof specs.",
                "Separate authoritative source record from proposed visual interpretation and preserve source silence.",
                "Use exact lettering text and explicit speaker ids; do not duplicate captions as dialogue.",
                "Use cinematic rhythm rather than a fixed panel count; identify every full-page immersive scene.",
                "Do not generate images, manuscript prose, PDF, print files or approvals.",
                "Record image and semantic visual review as BLOCKED_PROVIDER when no backend is configured.",
            ],
            "dossier_hash": dossier["dossier_hash"],
            "rules_hash": dossier["rules_hash"],
        }
        request["request_hash"] = content_hash(request)
        handoff, path = self.handoffs.prepare(
            book_id,
            "VISUAL_PREPRODUCTION",
            request,
            "art-iconography",
            [current["content_hash"], dossier["dossier_hash"], dossier["rules_hash"], *request["packet_hashes"], *review_hashes],
            writer_id=current["payload"].get("creator", {}).get("id"),
        )
        return {
            "status": handoff["status"],
            "book_id": book_id,
            "handoff_hash": handoff["handoff_hash"],
            "request_hash": request["request_hash"],
            "path": str(path),
            "required_role": "art-iconography",
            "images_requested": False,
        }

    def import_preproduction_handoff(self, book_id, handoff_path, response_path):
        _, dossier, packets = self._production_inputs(book_id)
        current, _ = self._pr5_review_gate(book_id)
        handoff = load_json(Path(handoff_path))
        response = load_json(Path(response_path))
        validate_named(handoff, self.root / "schemas" / "book-factory", "agent-handoff")
        validate_named(response, self.root / "schemas" / "book-factory", "agent-response")
        if handoff.get("book_id") != book_id or handoff.get("kind") != "VISUAL_PREPRODUCTION":
            raise ContractError("wrong visual-preproduction handoff")
        if finalize_handoff(handoff) != handoff:
            raise ContractError("visual-preproduction handoff content hash is invalid")
        if handoff["request"].get("manuscript_hash") != current["content_hash"]:
            raise ContractError("visual-preproduction handoff has a stale manuscript hash")
        if handoff["request"].get("dossier_hash") != dossier["dossier_hash"]:
            raise ContractError("visual-preproduction handoff has a stale dossier hash")
        execution = validate_execution(
            handoff, response, "visual_preproduction",
            writer_id=handoff.get("required_independence_from_writer_id"),
        )
        package = response.get("result", {}).get("preproduction")
        if not isinstance(package, dict):
            raise ContractError("agent response has no structured visual-preproduction package")
        if package.get("book_id") != book_id or package.get("manuscript_hash") != current["content_hash"]:
            raise ContractError("visual-preproduction package identity is stale")
        if package.get("proof_package", {}).get("storyboard_hash") != content_hash(package.get("storyboard")):
            raise ContractError("proof specifications do not bind the storyboard payload")
        required_events = [event["id"] for packet in packets for event in packet.get("events", [])]
        qa = validate_preproduction_package(
            package, required_events, current["payload"], current["content_hash"]
        )
        if qa["result"] != "PASS":
            raise ContractError("visual-preproduction package failed deterministic validation", {"findings": qa["findings"]})
        schema_root = self.root / "schemas" / "book-factory"
        validate_named(package["character_bible"], schema_root, "character-bible")
        validate_named(package["location_bible"], schema_root, "location-bible")
        validate_named(package["storyboard"], schema_root, "storyboard")
        validate_named(package["typography"], schema_root, "typography")
        validate_named(package["proof_package"], schema_root, "proof-spec")

        existing_components = (
            CharacterBibleVersionStore(self.books_root).versions(book_id),
            LocationBibleVersionStore(self.books_root).versions(book_id),
            StoryboardVersionStore(self.books_root).versions(book_id),
            TypographyVersionStore(self.books_root).versions(book_id),
            ProofSpecVersionStore(self.books_root).versions(book_id),
        )
        component_payloads = (
            package["character_bible"], package["location_bible"], package["storyboard"],
            package["typography"], package["proof_package"],
        )
        if all(records and records[-1]["payload"] == payload for records, payload in zip(existing_components, component_payloads)):
            status_path = self.books_root / book_id / "production-status.json"
            return {
                "status": load_json(status_path)["exact_result"],
                "book_id": book_id,
                "idempotent_replay": True,
                "publication_gate": "BLOCKED",
            }

        stores_and_payloads = [
            (CharacterBibleVersionStore(self.books_root), package["character_bible"]),
            (LocationBibleVersionStore(self.books_root), package["location_bible"]),
            (StoryboardVersionStore(self.books_root), package["storyboard"]),
            (TypographyVersionStore(self.books_root), package["typography"]),
            (ProofSpecVersionStore(self.books_root), package["proof_package"]),
        ]
        component_records = []
        for store, payload in stores_and_payloads:
            existing = store.versions(book_id)
            if existing and existing[-1]["payload"] == payload:
                component_records.append(existing[-1])
                continue
            parent_hash = existing[-1]["content_hash"] if existing else None
            component_records.append(store.put(book_id, payload, parent_hash=parent_hash))
        component_hashes = {
            "character_bible": component_records[0]["content_hash"],
            "location_bible": component_records[1]["content_hash"],
            "storyboard": component_records[2]["content_hash"],
            "typography": component_records[3]["content_hash"],
            "proof_specs": component_records[4]["content_hash"],
        }
        pages_root = self.books_root / book_id / "page-scripts"
        for page in package["storyboard"]["pages"]:
            validate_named(page, schema_root, "page-script")
            path = pages_root / ("page-%04d.v%04d.json" % (page["page_number"], package["storyboard"]["version"]))
            if path.exists() and load_json(path) != page:
                raise ContractError("immutable page script already differs", {"path": str(path)})
            if not path.exists():
                atomic_json_write(path, page)

        semantic_request = build_semantic_visual_review_request(
            package["proof_package"], self.providers.capabilities()["visual_evaluation"]
        )
        preproduction_review = {
            "schema_version": "1.0",
            "book_id": book_id,
            "result": "PASS",
            "review_kind": "DETERMINISTIC_SPECIFICATION_REVIEW",
            "reviewer": {
                "id": execution["agent_id"],
                "role": execution.get("role", "art-iconography"),
                "capability_verified": True,
                "execution_mechanism": execution["mechanism"],
            },
            "manuscript_hash": current["content_hash"],
            "component_hashes": component_hashes,
            "component_reports": qa["components"],
            "semantic_visual_review": semantic_request,
            "semantic_visual_approval_claimed": False,
            "images_generated": False,
            "pdf_generated": False,
            "publication_readiness_certified": False,
        }
        validate_named(preproduction_review, schema_root, "preproduction-review")
        review_store = PreproductionReviewVersionStore(self.books_root)
        prior = review_store.versions(book_id)
        review_record = review_store.put(book_id, preproduction_review, prior[-1]["content_hash"] if prior else None)
        response_record, stored_response_path = self.handoffs.store_response(handoff, response)

        state_store = StateStore(self.books_root, book_id, self._configuration()["retry_limits"]["stage"])
        state = state_store.load()
        transitions = (
            ("EDITORIAL_QA", "STORYBOARD", component_hashes["storyboard"]),
            ("STORYBOARD", "CHARACTER_BIBLE", component_hashes["character_bible"]),
            ("CHARACTER_BIBLE", "ART_PROOFS", component_hashes["proof_specs"]),
        )
        for source, target, output_hash in transitions:
            if state["current_stage"] == source:
                state = state_store.transition(
                    target,
                    "pr5-%s-%s" % (target.lower(), output_hash),
                    actor=execution["agent_id"],
                    input_hashes=handoff["locked_input_hashes"],
                    output_hashes=[output_hash],
                    policy_hashes=[dossier["rules_hash"]],
                )
        status = {
            "schema_version": "1.0",
            "book_id": book_id,
            "source_readiness": dossier["status"],
            "private_draft_gate": self.clearances.latest(book_id)["private_draft_gate"],
            "manuscript_draft_completion": "COMPLETE_PR5_LATEST_REVISION",
            "manuscript_v3_hash": ManuscriptVersionStore(self.books_root).versions(book_id)[2]["content_hash"],
            "latest_manuscript_version": current["version"],
            "independent_editorial_review": "PASS_DUAL_PERSPECTIVE",
            "visual_preproduction": "PASS_DETERMINISTIC_SPECIFICATION_REVIEW",
            "visual_proof_generation": "BLOCKED_PROVIDER",
            "semantic_visual_review": "NOT_EXECUTED_NO_IMAGES_OR_BACKEND",
            "visual_production": "NOT_STARTED_PR5_BOUNDARY",
            "publication_readiness": "BLOCKED",
            "publication_blockers": [
                "WORLDWIDE_OR_TARGET_MARKET_PUBLICATION_RIGHTS_NOT_CLEARED",
                "CHAPTER_EXTRACTION_ATOMICALLY_PARTIAL",
                "INDEPENDENT_FULL_ARC_SOURCE_APPROVAL_NOT_ESTABLISHED",
                "IMAGE_PROVIDER_NOT_CONFIGURED",
                "VISUAL_SEMANTIC_REVIEW_NOT_EXECUTED",
                "TYPOGRAPHY_FONT_LICENSE_SELECTION_PENDING",
                "TRIM_BLEED_AND_EXPORT_PROFILE_NOT_SPECIFIED",
                "FULL_ILLUSTRATION_PDF_AND_PUBLICATION_OUTSIDE_PR5",
            ],
            "latest_manuscript_hash": current["content_hash"],
            "component_hashes": component_hashes,
            "preproduction_review_hash": review_record["content_hash"],
            "scripted_pages": len(package["storyboard"]["pages"]),
            "full_page_immersive_scenes": [
                page["page_number"] for page in package["storyboard"]["pages"]
                if page.get("layout", {}).get("type") == "FULL_PAGE"
            ],
            "proof_specs": len(package["proof_package"]["specs"]),
            "run_stage": state["current_stage"],
            "exact_result": "VISUAL_PREPRODUCTION_REVIEWED_PUBLICATION_BLOCKED",
        }
        status["status_hash"] = content_hash(status)
        atomic_json_write(self.books_root / book_id / "production-status.json", status)
        return {
            "status": status["exact_result"],
            "book_id": book_id,
            "component_hashes": component_hashes,
            "preproduction_review_hash": review_record["content_hash"],
            "response_path": str(stored_response_path),
            "deterministic_review": qa,
            "semantic_visual_review": semantic_request,
            "run_stage": state["current_stage"],
            "images_generated": False,
            "pdf_generated": False,
            "publication_gate": "BLOCKED",
        }

    def image_capabilities(self):
        path = self.root / "book-factory" / "config" / "image-provider-capabilities.json"
        if path.is_file():
            report = load_json(path)
            supplied = report.pop("capability_hash", None)
            digest = content_hash(report)
            if supplied and supplied != digest:
                raise ContractError("image provider capability hash is invalid")
            report["capability_hash"] = digest
            return report
        return discover_image_backends(builtin_available=False)

    def visual_gold_standard(self, require_source_assets=False):
        """Verify actual curated pages; never reconstruct a missing benchmark."""
        return validate_gold_standard(self.root, require_source_assets=require_source_assets)

    def prepare_proof_recovery(self, book_id):
        """Persist four non-executable, parent-linked PR8 recovery requests."""
        return prepare_recovery_requests(self.root, book_id)

    def _pr6_components(self, book_id):
        if book_id == "DM08":
            raise ContractError("DM08 is an immutable existing edition and cannot enter proof generation")
        manuscripts = ManuscriptVersionStore(self.books_root).versions(book_id)
        characters = CharacterBibleVersionStore(self.books_root).versions(book_id)
        locations = LocationBibleVersionStore(self.books_root).versions(book_id)
        storyboards = StoryboardVersionStore(self.books_root).versions(book_id)
        proofs = ProofSpecVersionStore(self.books_root).versions(book_id)
        if not all((manuscripts, characters, locations, storyboards, proofs)):
            raise ContractError("PR6 requires the complete immutable PR5 package")
        state = StateStore(self.books_root, book_id, self._configuration()["retry_limits"]["stage"]).load()
        if state["current_stage"] not in {"ART_PROOFS", "AWAITING_STYLE_APPROVAL"}:
            raise ContractError("PR6 proof work requires ART_PROOFS or AWAITING_STYLE_APPROVAL state")
        return {
            "manuscript": manuscripts[-1],
            "character": characters[-1],
            "location": locations[-1],
            "storyboard": storyboards[-1],
            "proofs": proofs[-1],
            "state": state,
        }

    def _pr6_character_registry(self, book_id, components):
        payload = build_character_reference_registry(book_id, components["character"])
        return store_snapshot(CharacterReferenceVersionStore, self.books_root, book_id, payload)

    @staticmethod
    def _proof_page_number(kind):
        mapping = {
            "QUIET_CONVERSATION": 1,
            "DIVINE_REVEAL": 4,
            "BATTLE": 17,
            "FULL_PAGE_IMMERSION": 29,
        }
        if kind not in mapping:
            raise ContractError("unknown locked proof kind")
        return mapping[kind]

    def prepare_proof_generation(self, book_id, proof_id):
        components = self._pr6_components(book_id)
        capability_report = self.image_capabilities()
        selected_id = capability_report.get("selected_provider_id")
        capability = next(
            (item for item in capability_report.get("candidates", []) if item.get("provider_id") == selected_id),
            None,
        )
        if not capability or not capability.get("available") or not capability.get("actual_creation_executable"):
            raise ProviderUnavailableError(
                "no authorized executable image backend is available",
                capability_report,
            )
        specs = [item for item in components["proofs"]["payload"]["specs"] if item.get("id") == proof_id]
        if len(specs) != 1:
            raise ContractError("proof id is not unique in the active locked package")
        proof_spec = specs[0]
        page_number = self._proof_page_number(proof_spec["kind"])
        page = next(
            item for item in components["storyboard"]["payload"]["pages"]
            if item["page_number"] == page_number
        )
        location = next(
            item for item in components["location"]["payload"]["entries"]
            if item["id"] == proof_spec["setting"]
        )
        registry_record = self._pr6_character_registry(book_id, components)
        ledger = ProofExecutionLedger(self.books_root, book_id)
        prior_intents = [
            item for item in ledger.events()
            if item.get("proof_id") == proof_id and item.get("status") == "INTENT_RECORDED"
        ]
        prior_visual_review_hash = None
        revision_findings = []
        if prior_intents:
            prior_receipt = next(
                (item for item in self._latest_successful_receipts(book_id) if item["proof_id"] == proof_id),
                None,
            )
            if prior_receipt is None:
                raise ContractError("retry requires a completed prior proof image")
            prior_reviews = [
                item["payload"] for item in VisualReviewVersionStore(self.books_root).versions(book_id)
                if item["payload"].get("image", {}).get("sha256") == prior_receipt["image"]["sha256"]
            ]
            if not prior_reviews:
                raise ContractError("retry requires independent review of the exact prior proof image")
            prior_review = prior_reviews[-1]
            if prior_review.get("result") != "FIX":
                raise ContractError("retry is allowed only when the exact prior image received FIX")
            prior_visual_review_hash = prior_review["review_hash"]
            revision_findings = [
                "%s: %s" % (item.get("code", "REVIEW_FINDING"), item.get("message", ""))
                for item in prior_review.get("findings", [])
            ]
            if not revision_findings:
                revision_findings = [
                    "%s: %s" % (assessment["dimension"], finding)
                    for assessment in prior_review.get("dimension_assessments", [])
                    for finding in assessment.get("findings", [])
                    if assessment.get("result") == "FIX"
                ]
        existing_reference_paths = [
            reference["image_path"]
            for entry in registry_record["payload"]["entries"]
            if entry["canonical_character_id"] in proof_spec["character_ids"]
            for reference in entry.get("approved_visual_references", [])
        ]
        request = build_generation_request(
            book_id,
            proof_spec,
            page,
            registry_record["payload"],
            location,
            capability,
            components["proofs"]["content_hash"],
            components["manuscript"]["content_hash"],
            rules_status(self.root)["sha256"],
            len(prior_intents) + 1,
            existing_reference_paths,
            prior_visual_review_hash,
            revision_findings,
        )
        spending = load_json(self.root / "book-factory" / "policies" / "spending-policy.json")
        prepared = ledger.prepare(request, spending)
        return {
            "status": "READY_FOR_CODEX_NATIVE_IMAGE_TOOL",
            "book_id": book_id,
            "proof_id": proof_id,
            "provider": capability,
            "request": request,
            "request_path": prepared["request_path"],
            "idempotent_replay": prepared["idempotent"],
            "actual_cost_authorized_minor_units": 0,
            "paid_calls_authorized": False,
        }

    def import_proof_image(self, book_id, request_path, image_path, provider_receipt_path):
        components = self._pr6_components(book_id)
        request = load_json(Path(request_path))
        if request.get("request_hash") != content_hash({key: value for key, value in request.items() if key != "request_hash"}):
            raise ContractError("proof request content hash is invalid")
        if request.get("proof_package_hash") != components["proofs"]["content_hash"]:
            raise ContractError("proof request is stale against the locked proof package")
        provider_receipt = load_json(Path(provider_receipt_path))
        ledger = ProofExecutionLedger(self.books_root, book_id)
        receipt, replay = ledger.import_image(request, image_path, provider_receipt)
        successful = [
            load_json(path) for path in sorted((self.books_root / book_id / "illustration-proofs" / "receipts").glob("*.json"))
        ]
        snapshot = {
            "schema_version": "1.0",
            "book_id": book_id,
            "proof_package_hash": components["proofs"]["content_hash"],
            "provider_capability_hash": self.image_capabilities().get("capability_hash"),
            "receipts": sorted(successful, key=lambda item: (item["proof_id"], item["attempt_number"])),
            "validation": validate_proof_receipts(self.root, successful),
        }
        record = store_snapshot(IllustrationProofVersionStore, self.books_root, book_id, snapshot)
        return {
            "status": receipt["status"],
            "book_id": book_id,
            "proof_id": receipt["proof_id"],
            "image": receipt["image"],
            "receipt_hash": receipt["receipt_hash"],
            "proof_record_hash": record["content_hash"],
            "idempotent_replay": replay,
            "actual_cost_minor_units": receipt["actual_cost_minor_units"],
        }

    def _latest_successful_receipts(self, book_id):
        root = self.books_root / book_id / "illustration-proofs" / "receipts"
        receipts = [load_json(path) for path in sorted(root.glob("*.json"))]
        latest = {}
        for receipt in receipts:
            current = latest.get(receipt["proof_id"])
            if current is None or receipt["attempt_number"] > current["attempt_number"]:
                latest[receipt["proof_id"]] = receipt
        return [latest[key] for key in sorted(latest)]

    def _all_successful_receipts(self, book_id):
        root = self.books_root / book_id / "illustration-proofs" / "receipts"
        return [load_json(path) for path in sorted(root.glob("*.json"))]

    def prepare_visual_review(self, book_id, proof_id):
        self._pr6_components(book_id)
        receipt = next(
            (item for item in self._latest_successful_receipts(book_id) if item["proof_id"] == proof_id),
            None,
        )
        if receipt is None:
            raise ContractError("visual review requires a real generated proof image")
        request = visual_review_request(receipt)
        handoff, path = self.handoffs.prepare(
            book_id,
            "VISUAL_REVIEW",
            request,
            "typesetter-independent-qa",
            [receipt["image"]["sha256"], receipt["proof_spec_hash"], *receipt["source_hashes"].values()],
            writer_id=receipt["producer"]["id"],
        )
        return {
            "status": handoff["status"],
            "book_id": book_id,
            "proof_id": proof_id,
            "handoff_hash": handoff["handoff_hash"],
            "request_hash": request["request_hash"],
            "path": str(path),
            "actual_pixels_required": True,
            "required_independence_from_producer_id": receipt["producer"]["id"],
        }

    def import_visual_review(self, book_id, handoff_path, response_path):
        self._pr6_components(book_id)
        handoff = load_json(Path(handoff_path))
        response = load_json(Path(response_path))
        validate_named(handoff, self.root / "schemas" / "book-factory", "agent-handoff")
        validate_named(response, self.root / "schemas" / "book-factory", "agent-response")
        if handoff.get("book_id") != book_id or handoff.get("kind") != "VISUAL_REVIEW":
            raise ContractError("wrong visual-review handoff")
        if finalize_handoff(handoff) != handoff:
            raise ContractError("visual-review handoff content hash is invalid")
        execution = validate_execution(
            handoff,
            response,
            "visual_evaluation",
            writer_id=handoff.get("required_independence_from_writer_id"),
        )
        review_input = response.get("result", {}).get("visual_review")
        if not isinstance(review_input, dict):
            raise ContractError("agent response has no structured visual review")
        review_input = deepcopy(review_input)
        review_input["request_hash"] = handoff["request_hash"]
        review_input["reviewer"] = {
            "id": execution["agent_id"],
            "role": execution.get("role", "typesetter-independent-qa"),
            "capability_verified": True,
            "execution_mechanism": execution["mechanism"],
        }
        review_store = VisualReviewVersionStore(self.books_root)
        prior_for_request = [
            item for item in review_store.versions(book_id)
            if item["payload"].get("request_hash") == handoff["request_hash"]
        ]
        if prior_for_request:
            record = prior_for_request[-1]
            record_payload = record["payload"]
            comparable_keys = {
                "result", "actual_pixels_inspected", "dimension_assessments", "findings", "reviewer"
            }
            if any(record_payload.get(key) != review_input.get(key) for key in comparable_keys):
                raise ContractError("visual-review handoff already has a different immutable response")
        else:
            record_payload = finalize_visual_review(handoff["request"], review_input, self.root)
            record = store_snapshot(VisualReviewVersionStore, self.books_root, book_id, record_payload)
        response_record, stored_response_path = self.handoffs.store_response(handoff, response)
        latest_receipts = self._latest_successful_receipts(book_id)
        all_reviews = [item["payload"] for item in VisualReviewVersionStore(self.books_root).versions(book_id)]
        review_by_image = {item["image"]["sha256"]: item for item in all_reviews}
        latest_reviews = [review_by_image.get(item["image"]["sha256"]) for item in latest_receipts]
        required_proofs = {
            item["id"] for item in self._pr6_components(book_id)["proofs"]["payload"]["specs"]
        }
        if (
            {item["proof_id"] for item in latest_receipts} == required_proofs
            and all(latest_reviews)
        ):
            prior_status = load_json(self.books_root / book_id / "production-status.json")
            aggregate_result = "PASS" if all(item["result"] == "PASS" for item in latest_reviews) else "FIX"
            attempts = [
                item for item in ProofExecutionLedger(self.books_root, book_id).events()
                if item.get("status") == "INTENT_RECORDED"
            ]
            status = dict(prior_status)
            status.update({
                "visual_proof_generation": "COMPLETE_FOUR_REAL_PROOFS",
                "semantic_visual_review": "%s_INDEPENDENT_EXACT_IMAGE_REVIEW" % aggregate_result,
                "visual_production": "PROOFS_ONLY_FULL_BOOK_NOT_STARTED",
                "style_approval": (
                    "ELIGIBLE_TO_PREPARE_HUMAN_REQUEST" if aggregate_result == "PASS"
                    else "BLOCKED_PROOF_FIXES_AND_RETRY_CEILING"
                ),
                "proof_images_latest": len(latest_receipts),
                "real_images_generated_total": len(attempts),
                "proof_image_hashes": [item["image"]["sha256"] for item in latest_receipts],
                "visual_review_hashes": [item["review_hash"] for item in latest_reviews],
                "actual_spending_minor_units": sum(
                    item["actual_cost_minor_units"] for item in self._all_successful_receipts(book_id)
                ),
                "run_stage": "ART_PROOFS",
                "exact_result": (
                    "ILLUSTRATION_PROOFS_REVIEWED_PASS_STYLE_REQUEST_NOT_YET_PREPARED_PUBLICATION_BLOCKED"
                    if aggregate_result == "PASS"
                    else "ILLUSTRATION_PROOFS_REVIEWED_FIX_RETRY_EXHAUSTED_PUBLICATION_BLOCKED"
                ),
            })
            status["publication_blockers"] = [
                item for item in prior_status.get("publication_blockers", [])
                if item not in {
                    "IMAGE_PROVIDER_NOT_CONFIGURED",
                    "VISUAL_SEMANTIC_REVIEW_NOT_EXECUTED",
                    "FULL_ILLUSTRATION_PDF_AND_PUBLICATION_OUTSIDE_PR5",
                    "FULL_ILLUSTRATION_PDF_AND_PUBLICATION_OUTSIDE_PR6",
                    "PROOF_FIXES_REQUIRED_RETRY_CEILING_EXHAUSTED",
                }
            ]
            status["publication_blockers"].append("FULL_ILLUSTRATION_PDF_AND_PUBLICATION_OUTSIDE_PR6")
            if aggregate_result == "FIX":
                status["publication_blockers"].append("PROOF_FIXES_REQUIRED_RETRY_CEILING_EXHAUSTED")
            status.pop("status_hash", None)
            status["status_hash"] = content_hash(status)
            atomic_json_write(self.books_root / book_id / "production-status.json", status)
        return {
            "status": record_payload["result"],
            "book_id": book_id,
            "proof_id": record_payload["proof_id"],
            "image_hash": record_payload["image"]["sha256"],
            "review_hash": record_payload["review_hash"],
            "review_version_hash": record["content_hash"],
            "response_hash": response_record["response_hash"],
            "response_path": str(stored_response_path),
            "approval_claimed": False,
        }

    def build_proof_contact_sheet(self, book_id):
        components = self._pr6_components(book_id)
        receipts = self._latest_successful_receipts(book_id)
        reviews = [item["payload"] for item in VisualReviewVersionStore(self.books_root).versions(book_id)]
        validation = validate_proof_receipts(self.root, receipts)
        if validation["result"] != "PASS":
            raise ContractError("proof files fail deterministic validation", {"findings": validation["findings"]})
        destination = self.books_root / book_id / "illustration-proofs" / "contact-sheets" / "pr6-proof-contact-sheet.svg"
        metadata = build_contact_sheet_svg(self.root, receipts, reviews, destination)
        status_path = self.books_root / book_id / "production-status.json"
        if status_path.exists():
            status = load_json(status_path)
            status["contact_sheet_hash"] = metadata["contact_sheet_hash"]
            status["contact_sheet_path"] = metadata["contact_sheet_path"]
            status.pop("status_hash", None)
            status["status_hash"] = content_hash(status)
            atomic_json_write(status_path, status)
        return {
            "status": "CONTACT_SHEET_READY",
            "book_id": book_id,
            "path": str(destination),
            "metadata_path": str(destination.with_suffix(".json")),
            "contact_sheet": metadata,
            "proof_package_hash": components["proofs"]["content_hash"],
        }

    def prepare_style_approval(self, book_id):
        components = self._pr6_components(book_id)
        receipts = self._latest_successful_receipts(book_id)
        required_proofs = {item["id"] for item in components["proofs"]["payload"]["specs"]}
        if {item["proof_id"] for item in receipts} != required_proofs:
            raise ContractError("style approval requires all four locked proof images")
        validation = validate_proof_receipts(self.root, receipts)
        if validation["result"] != "PASS":
            raise ContractError("style approval requires deterministic proof validation PASS")
        reviews = [item["payload"] for item in VisualReviewVersionStore(self.books_root).versions(book_id)]
        latest_review_by_image = {item["image"]["sha256"]: item for item in reviews}
        if any(latest_review_by_image.get(item["image"]["sha256"], {}).get("result") != "PASS" for item in receipts):
            raise ContractError("style approval requires independent PASS review for every exact proof image")
        contact = self.build_proof_contact_sheet(book_id)["contact_sheet"]
        registry = self._pr6_character_registry(book_id, components)
        request = build_style_approval_request(
            book_id,
            receipts,
            [latest_review_by_image[item["image"]["sha256"]] for item in receipts],
            registry["content_hash"],
            components["proofs"]["content_hash"],
            {
                "manuscript_hash": components["manuscript"]["content_hash"],
                "source_graph_hash": self.graph.graph_hash(),
                "rules_hash": rules_status(self.root)["sha256"],
            },
            contact,
        )
        approval_record = store_snapshot(
            StyleApprovalRequestVersionStore, self.books_root, book_id, request
        )
        state_store = StateStore(self.books_root, book_id, self._configuration()["retry_limits"]["stage"])
        state = state_store.load()
        if state["current_stage"] == "ART_PROOFS":
            state = state_store.transition(
                "AWAITING_STYLE_APPROVAL",
                "pr6-awaiting-style-%s" % request["approval_request_hash"],
                actor="director",
                input_hashes=[components["proofs"]["content_hash"], registry["content_hash"], *[item["image"]["sha256"] for item in receipts]],
                output_hashes=[approval_record["content_hash"], contact["contact_sheet_hash"]],
                policy_hashes=[rules_status(self.root)["sha256"]],
            )
        total_spend = sum(
            item["actual_cost_minor_units"] for item in self._all_successful_receipts(book_id)
        )
        prior_status = load_json(self.books_root / book_id / "production-status.json")
        status = dict(prior_status)
        status.update({
            "visual_proof_generation": "COMPLETE_FOUR_REAL_PROOFS",
            "semantic_visual_review": "PASS_INDEPENDENT_EXACT_IMAGE_REVIEW",
            "visual_production": "PROOFS_ONLY_FULL_BOOK_NOT_STARTED",
            "style_approval": "AWAITING_HUMAN_STYLE_APPROVAL",
            "proof_images": len(receipts),
            "proof_image_hashes": [item["image"]["sha256"] for item in receipts],
            "visual_review_hashes": [latest_review_by_image[item["image"]["sha256"]]["review_hash"] for item in receipts],
            "contact_sheet_hash": contact["contact_sheet_hash"],
            "style_approval_request_hash": approval_record["content_hash"],
            "actual_spending_minor_units": total_spend,
            "run_stage": state["current_stage"],
            "exact_result": "ILLUSTRATION_PROOFS_READY_AWAITING_STYLE_APPROVAL_PUBLICATION_BLOCKED",
        })
        status["publication_blockers"] = [
            item for item in prior_status.get("publication_blockers", [])
            if item not in {"IMAGE_PROVIDER_NOT_CONFIGURED", "VISUAL_SEMANTIC_REVIEW_NOT_EXECUTED"}
        ] + ["HUMAN_VISUAL_STYLE_APPROVAL_PENDING"]
        status.pop("status_hash", None)
        status["status_hash"] = content_hash(status)
        atomic_json_write(self.books_root / book_id / "production-status.json", status)
        return {
            "status": request["status"],
            "book_id": book_id,
            "approval_request_hash": request["approval_request_hash"],
            "approval_version_hash": approval_record["content_hash"],
            "contact_sheet": contact,
            "proof_count": len(receipts),
            "actual_spending_minor_units": total_spend,
            "run_stage": state["current_stage"],
            "publication_gate": "BLOCKED",
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

    def produce_next(self, dry_run=False, fixture_mode=False, fixture_plan_path=None):
        result = self.orchestrator.produce_next(
            fixture_mode=fixture_mode,
            fixture_plan_path=fixture_plan_path,
            select_only=bool(dry_run),
        )
        if result["status"] == "NO_ELIGIBLE_BOOKS" and dry_run:
            result["status"] = "NO_READY_BOOKS"
            result["selected_book"] = None
            result["standards"] = rules_status(self.root)
        return result

    def produce_book(self, book_id, fixture_mode=False, fixture_plan_path=None):
        return self.orchestrator.produce_book(book_id, fixture_mode, fixture_plan_path)

    def resume_book(self, book_id, fixture_mode=False, fixture_plan_path=None):
        return self.orchestrator.resume_book(book_id, fixture_mode, fixture_plan_path)

    def prepare_production_slice(self, book_id):
        if book_id != "DM04":
            raise ContractError("PR10 real-production slice is locked to DM04", {"book_id": book_id})
        return self.real_production.prepare()

    def production_slice_status(self, book_id):
        if book_id != "DM04":
            raise ContractError("PR10 real-production slice is locked to DM04", {"book_id": book_id})
        return self.real_production.status()

    def import_production_campaign_approval(self, book_id, approval_path):
        if book_id != "DM04":
            raise ContractError("PR10 campaign approval is locked to DM04", {"book_id": book_id})
        return self.real_production.import_campaign_approval(approval_path)

    def prepare_production_generation(self, book_id, page_id):
        if book_id != "DM04":
            raise ContractError("PR10 generation is locked to DM04", {"book_id": book_id})
        return self.real_production.prepare_generation(page_id)

    def import_production_image(self, book_id, page_id, request_path, image_path, provider_receipt_path):
        if book_id != "DM04":
            raise ContractError("PR11 image import is locked to DM04", {"book_id": book_id})
        return self.real_production.import_image(
            page_id, request_path, image_path, provider_receipt_path
        )

    def prepare_production_visual_review(self, book_id, page_id):
        if book_id != "DM04":
            raise ContractError("PR11 visual review is locked to DM04", {"book_id": book_id})
        return self.real_production.prepare_visual_review(page_id)

    def import_production_visual_review(self, book_id, page_id, request_path, response_path):
        if book_id != "DM04":
            raise ContractError("PR11 visual review import is locked to DM04", {"book_id": book_id})
        return self.real_production.import_visual_review(page_id, request_path, response_path)

    def factory_queue(self, fixture_mode=False):
        return self.orchestrator.queue(fixture_mode)

    def factory_blocked(self, fixture_mode=False):
        return self.orchestrator.blocked(fixture_mode)

    def factory_approvals(self, fixture_mode=False):
        return self.orchestrator.approvals(fixture_mode)

    def factory_costs(self, fixture_mode=False):
        return self.orchestrator.costs(fixture_mode)

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
        if state["current_stage"] in {"STORYBOARD", "CHARACTER_BIBLE", "ART_PROOFS"}:
            status_path = self.books_root / book_id / "production-status.json"
            if status_path.exists():
                status = load_json(status_path)
                return {
                    "status": status["exact_result"],
                    "book_id": book_id,
                    "current_stage": state["current_stage"],
                    "production_status": status,
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

    def _page_engine_gate(self, book_id, required_stage, fixture_mode, private_preview=False):
        if fixture_mode:
            return {"mode": "ISOLATED_FIXTURE", "publication_eligible": False, "state_mutation_allowed": False}
        book = self.catalogue.get(book_id)
        if book is None:
            raise ContractError("book is not in the authoritative catalogue", {"book_id": book_id})
        if book_id == "DM08" or book.get("edition_status") == "EXISTING_EDITION":
            raise ContractError("existing reference editions cannot enter page production", {"book_id": book_id})
        if private_preview:
            return {"mode": "PRIVATE_PREVIEW", "publication_eligible": False, "state_mutation_allowed": False}
        store = StateStore(self.books_root, book_id, self._configuration()["retry_limits"]["stage"])
        if not store.events_path.is_file():
            raise ContractError("page production requires durable book state", {"book_id": book_id})
        state = store.load()
        required_stages = (required_stage,) if isinstance(required_stage, str) else tuple(required_stage)
        if state["current_stage"] not in required_stages:
            raise ContractError(
                "page-engine lifecycle gate is closed",
                {"book_id": book_id, "required_stages": list(required_stages), "current_stage": state["current_stage"]},
            )
        return {"mode": "PRODUCTION", "publication_eligible": False, "state_mutation_allowed": True, "state": state}

    def compose_page(self, spec_path, output_dir, fixture_mode=False, private_preview=False):
        spec = load_json(Path(spec_path))
        gate = self._page_engine_gate(spec.get("book_id"), ("LETTERING", "PDF_LAYOUT", "VISUAL_QA"), fixture_mode, private_preview)
        result = render_page(
            spec, self.root, Path(output_dir), fixture_mode,
            self.root / "book-factory" / "config" / "page-renderer-fonts.json",
            private_preview,
        )
        if not fixture_mode and not private_preview:
            composition = load_json(Path(result["composition"]))
            store = PageCompositionVersionStore(self.books_root)
            prior = store.versions(spec["book_id"], spec["page_id"])
            record = store.put(spec["book_id"], spec["page_id"], composition, prior[-1]["content_hash"] if prior else None)
            result["version_record_hash"] = record["content_hash"]
            result["artifact"] = ArtifactStore(self.books_root).put(
                Path(result["rendered_png"]).read_bytes(), media_type="image/png", extension="png",
                logical_id=spec["page_id"], input_hashes=[composition["composition_hash"]], version=record["version"],
            )
        result["gate"] = gate
        return result

    def validate_page(self, composition_path, fixture_mode=False, private_preview=False):
        return validate_composition_file(composition_path, self.root, fixture_mode, private_preview)

    def compose_book(self, manifest_path, output_dir, fixture_mode=False):
        manifest = load_json(Path(manifest_path))
        gate = self._page_engine_gate(manifest.get("book_id"), ("LETTERING", "PDF_LAYOUT", "VISUAL_QA"), fixture_mode)
        result = render_book(
            manifest, self.root, Path(output_dir), fixture_mode,
            self.root / "book-factory" / "config" / "page-renderer-fonts.json",
        )
        if not fixture_mode:
            page_store = PageCompositionVersionStore(self.books_root)
            artifact_store = ArtifactStore(self.books_root)
            for page_result in result["pages"]:
                composition = load_json(Path(page_result["composition"]))
                page_id = composition["page_id"]
                prior = page_store.versions(manifest["book_id"], page_id)
                record = page_store.put(
                    manifest["book_id"], page_id, composition,
                    prior[-1]["content_hash"] if prior else None,
                )
                page_result["version_record_hash"] = record["content_hash"]
                page_result["artifact"] = artifact_store.put(
                    Path(page_result["rendered_png"]).read_bytes(), media_type="image/png", extension="png",
                    logical_id=page_id, input_hashes=[composition["composition_hash"]], version=record["version"],
                )
        if not fixture_mode and gate["state"]["current_stage"] == "LETTERING":
            state_store = StateStore(self.books_root, manifest["book_id"], self._configuration()["retry_limits"]["stage"])
            state = state_store.transition(
                "PDF_LAYOUT", "pr8-compose-book-%s" % load_json(Path(result["manifest"]))["manifest_hash"],
                actor="page-composition-engine", input_hashes=[page["storyboard_hash"] for page in manifest["pages"]],
                output_hashes=[load_json(Path(result["manifest"]))["manifest_hash"]],
            )
            result["run_stage"] = state["current_stage"]
        elif not fixture_mode:
            result["run_stage"] = gate["state"]["current_stage"]
            result["page_local_rebuild"] = True
        result["gate"] = gate
        return result

    def export_pdf(self, manifest_path, output_path, fixture_mode=False):
        manifest = load_json(Path(manifest_path))
        gate = self._page_engine_gate(manifest.get("book_id"), ("PDF_LAYOUT", "VISUAL_QA"), fixture_mode)
        result = build_reader_pdf(manifest, Path(output_path), fixture_mode)
        if not fixture_mode:
            record_payload = {
                "book_id": manifest["book_id"], "manifest_hash": manifest["manifest_hash"],
                "pdf_sha256": result["pdf_sha256"], "inspection": load_json(Path(result["inspection_path"])),
                "publication_eligible": False,
            }
            store = PdfArtifactVersionStore(self.books_root)
            prior = store.versions(manifest["book_id"])
            record = store.put(manifest["book_id"], record_payload, prior[-1]["content_hash"] if prior else None)
            result["version_record_hash"] = record["content_hash"]
            result["artifact"] = ArtifactStore(self.books_root).put(
                Path(result["pdf_path"]).read_bytes(), media_type="application/pdf", extension="pdf",
                logical_id="%s-digital-reader" % manifest["book_id"],
                input_hashes=[manifest["manifest_hash"]], version=record["version"],
            )
            if gate["state"]["current_stage"] == "PDF_LAYOUT":
                state_store = StateStore(self.books_root, manifest["book_id"], self._configuration()["retry_limits"]["stage"])
                state = state_store.transition(
                    "VISUAL_QA", "pr8-export-pdf-%s" % result["pdf_sha256"], actor="pdf-layout-engine",
                    input_hashes=[manifest["manifest_hash"]], output_hashes=[result["pdf_sha256"]],
                )
                result["run_stage"] = state["current_stage"]
            else:
                result["run_stage"] = "VISUAL_QA"
                result["page_local_rebuild"] = True
        result["gate"] = gate
        return result

    def inspect_pdf(self, pdf_path, manifest_path=None, fixture_mode=False):
        manifest = load_json(Path(manifest_path)) if manifest_path else None
        if manifest:
            self._page_engine_gate(manifest.get("book_id"), "VISUAL_QA", fixture_mode)
        result = inspect_reader_pdf(Path(pdf_path), manifest)
        result["semantic_visual_review"] = {
            "result": "NOT_APPLICABLE_SYNTHETIC_FIXTURE" if fixture_mode else "ESCALATE",
            "reason": "deterministic PDF inspection cannot certify iconography, composition, character continuity, crop safety or reading-size visual quality",
        }
        result["publication_state_transition"] = "PROHIBITED_FIXTURE" if fixture_mode else "BLOCKED_PENDING_INDEPENDENT_SEMANTIC_REVIEW"
        return result

    def resume_layout(self, book_id, composition_path=None, page_id=None, fixture_mode=False):
        if fixture_mode:
            if not composition_path:
                raise ContractError("fixture resume requires an explicit composition path")
            report = validate_composition_file(composition_path, self.root, True)
            return {
                "status": "RESUMED_IDEMPOTENTLY" if report["result"] == "PASS" else "FIX",
                "book_id": book_id, "composition_path": str(Path(composition_path)),
                "validation": report, "mutated": False, "publication_eligible": False,
            }
        self._page_engine_gate(book_id, ("LETTERING", "PDF_LAYOUT", "VISUAL_QA"), False)
        if not page_id:
            raise ContractError("production resume requires a stable page ID")
        versions = PageCompositionVersionStore(self.books_root).versions(book_id, page_id)
        if not versions:
            return {"status": "BLOCKED", "code": "NO_PAGE_COMPOSITION", "book_id": book_id, "mutated": False}
        return {
            "status": "RESUMED_IDEMPOTENTLY", "book_id": book_id, "page_id": page_id,
            "version": versions[-1]["version"], "composition_hash": versions[-1]["content_hash"],
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
        validate_named(
            load_json(self.root / "book-factory" / "references" / "visual-gold-standard" / "manifest.json"),
            schema_root, "visual-gold-standard",
        )
        validate_named(
            load_json(self.root / "book-factory" / "policies" / "indian-cultural-authenticity.json"),
            schema_root, "cultural-authenticity",
        )
        validate_named(
            load_json(self.root / "books" / "DM04" / "visual-comparisons" / "pr7-comparison.json"),
            schema_root, "visual-comparison",
        )
        image_capabilities = self.image_capabilities()
        if image_capabilities.get("selected_provider_id") != "codex-built-in-image-gen":
            raise ContractError("PR6 capability record must select the executed Codex native backend")
        fixture = load_json(self.root / "book-factory" / "fixtures" / "synthetic-book" / "catalogue.json")
        validate_named(fixture, schema_root, "catalogue")
        pr9_fixture_root = self.root / "book-factory" / "fixtures" / "autonomous-orchestration"
        pr9_fixture_catalogue = load_json(pr9_fixture_root / "catalogue.json")
        validate_named(pr9_fixture_catalogue, schema_root, "catalogue")
        pr9_fixture_plan = load_json(pr9_fixture_root / "lifecycle-plan.json")
        if pr9_fixture_plan.get("fixture") is not True or pr9_fixture_plan.get("publication_eligible") is not False:
            raise ContractError("PR9 fixture boundary is invalid")
        if set(pr9_fixture_plan.get("stages", {})) != set(self.orchestrator._fixture_plan(pr9_fixture_root / "lifecycle-plan.json")["stages"]):
            raise ContractError("PR9 fixture stage plan is incomplete")
        pr9_contracts = []
        for name in ("autonomous-director.json", "composed-page-visual-review.json", "page-local-recovery.json"):
            payload = load_json(self.root / "book-factory" / "contracts" / name)
            if payload.get("schema_version") != "1.0" or not payload.get("contract_id"):
                raise ContractError("PR9 contract is invalid", {"path": name})
            pr9_contracts.append(name)
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
        preproduction_versions = {
            "character_bibles": [], "location_bibles": [], "storyboards": [],
            "typography": [], "proof_specs": [], "preproduction_reviews": [],
            "character_references": [], "illustration_proof_records": [],
            "visual_reviews": [], "style_approval_requests": [],
            "proof_recovery_requests": [],
        }
        proof_execution_validation = []
        for book_root in sorted(path for path in self.books_root.iterdir() if path.is_dir() and path.name != "_artifacts"):
            for record in ManuscriptVersionStore(self.books_root).versions(book_root.name):
                validate_named(record["payload"], schema_root, "manuscript")
                manuscript_versions.append({"book_id": book_root.name, "content_hash": record["content_hash"]})
            for record in EditorialReviewStore(self.books_root).versions(book_root.name):
                validate_named(record["payload"], schema_root, "editorial-review")
                editorial_review_versions.append({"book_id": book_root.name, "content_hash": record["content_hash"]})
            component_stores = (
                ("character_bibles", CharacterBibleVersionStore(self.books_root), "character-bible"),
                ("location_bibles", LocationBibleVersionStore(self.books_root), "location-bible"),
                ("storyboards", StoryboardVersionStore(self.books_root), "storyboard"),
                ("typography", TypographyVersionStore(self.books_root), "typography"),
                ("proof_specs", ProofSpecVersionStore(self.books_root), "proof-spec"),
                ("preproduction_reviews", PreproductionReviewVersionStore(self.books_root), "preproduction-review"),
                ("character_references", CharacterReferenceVersionStore(self.books_root), "character-reference"),
                ("illustration_proof_records", IllustrationProofVersionStore(self.books_root), "illustration-proof-record"),
                ("visual_reviews", VisualReviewVersionStore(self.books_root), "visual-review"),
                ("style_approval_requests", StyleApprovalRequestVersionStore(self.books_root), "style-approval-request"),
                ("proof_recovery_requests", ProofRecoveryRequestVersionStore(self.books_root), "proof-recovery-campaign"),
            )
            for label, store, schema_name in component_stores:
                for record in store.versions(book_root.name):
                    validate_named(record["payload"], schema_root, schema_name)
                    preproduction_versions[label].append({
                        "book_id": book_root.name, "content_hash": record["content_hash"]
                    })
            receipt_root = book_root / "illustration-proofs" / "receipts"
            if receipt_root.is_dir():
                receipts = [load_json(path) for path in sorted(receipt_root.glob("*.json"))]
                proof_gate = validate_proof_receipts(self.root, receipts)
                if proof_gate["result"] != "PASS":
                    raise ContractError("stored illustration proof failed validation", {"book_id": book_root.name, "findings": proof_gate["findings"]})
                ledger = ProofExecutionLedger(self.books_root, book_root.name)
                events = ledger.events()
                proof_execution_validation.append({
                    "book_id": book_root.name,
                    "receipts": len(receipts),
                    "ledger_events": len(events),
                    "actual_cost_minor_units": sum(item.get("actual_cost_minor_units", 0) for item in receipts),
                    "result": proof_gate["result"],
                })
        pr7_validation = validate_pr7(self.root)
        font_resolution = FontResolver(
            self.root / "book-factory" / "config" / "page-renderer-fonts.json"
        ).resolve()
        demo_input = load_json(
            self.root / "book-factory" / "fixtures" / "page-engine" / "demo-book.json"
        )
        supplied_fixture_hash = demo_input.get("fixture_manifest_hash")
        if supplied_fixture_hash != content_hash({key: value for key, value in demo_input.items() if key != "fixture_manifest_hash"}):
            raise ContractError("PR8 fixture manifest hash is invalid")
        demo_pages = []
        for path in sorted((self.root / "output" / "page-engine-demo").glob("*.composition.json")):
            composition = load_json(path)
            validate_named(composition, schema_root, "page-composition")
            report = validate_composition_file(path, self.root, True)
            validate_named(report, schema_root, "page-render-report")
            if report["result"] != "PASS":
                raise ContractError("PR8 fixture page failed deterministic validation", {"path": str(path), "findings": report["findings"]})
            demo_pages.append({"page_id": composition["page_id"], "composition_hash": composition["composition_hash"]})
        if len(demo_pages) != 4:
            raise ContractError("PR8 requires exactly four committed technical demonstration pages")
        pdf_path = self.root / "output" / "pdf" / "khatakshetra-book-factory-non-production-renderer-test.pdf"
        composed_manifest = load_json(self.root / "output" / "page-engine-demo" / "composed-book-manifest.json")
        pdf_validation = inspect_reader_pdf(pdf_path, composed_manifest)
        validate_named(pdf_validation, schema_root, "pdf-artifact")
        if pdf_validation["result"] != "PASS":
            raise ContractError("PR8 technical demonstration PDF failed deterministic validation", {"findings": pdf_validation["findings"]})
        pr10 = None
        if (self.books_root / "DM04" / "production-slices" / "v0001.json").is_file():
            pr10 = self.real_production.validate()
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
            "preproduction_versions": preproduction_versions,
            "proof_execution_validation": proof_execution_validation,
            "catalogue_mapping_validation": mapping_validation,
            "input_report": self.input_report(),
            "image_capabilities": image_capabilities,
            "pr7": pr7_validation,
            "pr8": {
                "fixture_manifest_hash": demo_input["fixture_manifest_hash"],
                "technical_pages": demo_pages,
                "pdf": pdf_validation,
                "font": font_resolution,
                "publication_eligible": False,
                "semantic_visual_review": "NOT_APPLICABLE_TO_SYNTHETIC_FIXTURE_AND_NOT_CLAIMED_FOR_PRODUCTION",
            },
            "pr9": {
                "contracts": pr9_contracts,
                "fixture_catalogue_books": len(pr9_fixture_catalogue["books"]),
                "fixture_stages": list(pr9_fixture_plan["stages"]),
                "queue_catalogue_books": self.orchestrator.queue(False)["catalogue_count"],
                "production_fixture_isolation": "ENFORCED",
                "publication_eligible": False,
            },
            "pr10": pr10,
            "pr11": ({
                "status": pr10["status"],
                "actual_image_operations": pr10["actual_image_operations"],
                "actual_cost_minor_units": pr10["actual_cost_minor_units"],
                "publication_eligible": False,
            } if pr10 and pr10["actual_image_operations"] else None),
            "note": "PR11 executed the exact two-operation private DM04 pilot, imported independent actual-pixel FIX/ESCALATE reviews, and stopped without composition, PDF, publication, DM08 changes or source-graph mutation.",
        }
