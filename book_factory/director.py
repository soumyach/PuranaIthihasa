"""Single user-facing orchestration facade for Foundation PR3."""

import json
from pathlib import Path

from . import __version__
from .catalogue import CatalogueStore
from .catalogue_v01 import SourceMappingRegistry
from .contracts import load_schema, validate_named
from .drafting import build_manuscript_request
from .errors import ContractError, NotImplementedStageError
from .pilot import PilotSelector, catalogue_readiness_report
from .providers.base import FixtureImageProviderContract, ProviderRegistry
from .references import ReferenceEditionRegistry
from .rules import rules_status
from .source_graph import ReadOnlySourceGraph
from .source_intelligence import DossierStore, SourceReadinessAssessor, StoryPacketBuilder, StoryPacketStore
from .state import StateStore, next_stage
from .util import atomic_json_write, atomic_write, load_json, sha256_bytes


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
            "implementation": "FOUNDATION_PR3",
            "catalogue_books": len(books),
            "readiness_counts": {state: sum(book["readiness"] == state for book in books) for state in sorted({book["readiness"] for book in books})},
            "active_runs": states,
            "rules": rules_status(self.root),
            "providers": self.providers.capabilities(),
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

    def draft_manuscript(self, book_id, dry_run=False):
        manifest = self.catalogue.get(book_id)
        if manifest is None:
            raise ContractError("book %s is not in the catalogue" % book_id)
        dossier = self.source_intelligence.assess(manifest, self.mappings.resolve(book_id))
        request = build_manuscript_request(manifest, dossier, dossier["story_packets"], dossier["rules_hash"])
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
        return {
            "status": "PASS",
            "schemas": schemas,
            "worker_contracts": worker_contracts,
            "source_graph": {"passed": graph_report["passed"], "graph_hash": graph_report["graph_hash"]},
            "rules": rules_status(self.root),
            "reference_assets": reference_assets,
            "reference_editions": [dm08],
            "catalogue_mapping_validation": mapping_validation,
            "input_report": self.input_report(),
            "note": "Foundation PR3 prepares a source-controlled pilot packet but does not generate a manuscript, illustrations, or PDF",
        }
