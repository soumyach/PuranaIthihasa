"""Single user-facing orchestration facade for Foundation PR2."""

import json
from pathlib import Path

from . import __version__
from .catalogue import CatalogueStore
from .contracts import load_schema, validate_named
from .errors import ContractError, NotImplementedStageError
from .providers.base import FixtureImageProviderContract, ProviderRegistry
from .rules import rules_status
from .source_graph import ReadOnlySourceGraph
from .source_intelligence import DossierStore, SourceReadinessAssessor, StoryPacketBuilder
from .state import StateStore, next_stage
from .util import load_json, sha256_bytes


class FactoryDirector:
    def __init__(self, repository_root, catalogue_path=None):
        self.root = Path(repository_root).resolve()
        self.books_root = self.root / "books"
        self.catalogue = CatalogueStore(Path(catalogue_path).resolve() if catalogue_path else self.books_root / "catalogue.json")
        self.graph = ReadOnlySourceGraph(self.root / "research" / "source-graph")
        self.source_intelligence = SourceReadinessAssessor(self.graph, self.root)
        self.providers = ProviderRegistry({"image": FixtureImageProviderContract()})

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
            "implementation": "FOUNDATION_PR2",
            "catalogue_books": len(books),
            "readiness_counts": {state: sum(book["readiness"] == state for book in books) for state in sorted({book["readiness"] for book in books})},
            "active_runs": states,
            "rules": rules_status(self.root),
            "providers": self.providers.capabilities(),
            "configuration": self._configuration(),
            "publishing": "NOT_IMPLEMENTED",
            "inputs": self.input_report(),
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
            dossier = self.source_intelligence.assess(book)
            blockers = ["CATALOGUE_%s" % book["readiness"]] if book["readiness"] != "READY" else []
            blockers.extend(item["code"] for item in dossier["blockers"])
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
        dossier = self.source_intelligence.assess(manifest)
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

    def produce_next(self, dry_run=False):
        if not dry_run:
            raise NotImplementedStageError("Foundation PR2 supports produce-next only with --dry-run")
        selected = self.catalogue.select_next()
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
        return {
            "status": "NOT_IMPLEMENTED",
            "book_id": book_id,
            "current_stage": state["current_stage"],
            "requested_stage": target,
            "message": "Foundation PR2 does not execute production stages",
            "mutated": False,
        }

    def validate(self):
        self._configuration()
        catalogue = self.catalogue.load()
        schema_root = self.root / "schemas" / "book-factory"
        validate_named(catalogue, schema_root, "catalogue")
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
        return {
            "status": "PASS",
            "schemas": schemas,
            "worker_contracts": worker_contracts,
            "source_graph": {"passed": graph_report["passed"], "graph_hash": graph_report["graph_hash"]},
            "rules": rules_status(self.root),
            "reference_assets": reference_assets,
            "input_report": self.input_report(),
            "note": "Foundation PR2 validates readiness and editorial contracts but does not produce a book",
        }
