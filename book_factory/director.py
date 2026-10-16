"""Single user-facing orchestration facade for Foundation PR1."""

import json
from pathlib import Path

from . import __version__
from .catalogue import CatalogueStore
from .contracts import load_schema, validate_named
from .errors import ContractError, NotImplementedStageError
from .providers.base import FixtureImageProviderContract, ProviderRegistry
from .rules import rules_status
from .source_graph import ReadOnlySourceGraph
from .state import StateStore, next_stage
from .util import load_json


class FactoryDirector:
    def __init__(self, repository_root, catalogue_path=None):
        self.root = Path(repository_root).resolve()
        self.books_root = self.root / "books"
        self.catalogue = CatalogueStore(Path(catalogue_path).resolve() if catalogue_path else self.books_root / "catalogue.json")
        self.graph = ReadOnlySourceGraph(self.root / "research" / "source-graph")
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
            "implementation": "FOUNDATION_PR1",
            "catalogue_books": len(books),
            "readiness_counts": {state: sum(book["readiness"] == state for book in books) for state in sorted({book["readiness"] for book in books})},
            "active_runs": states,
            "rules": rules_status(self.root),
            "providers": self.providers.capabilities(),
            "configuration": self._configuration(),
            "publishing": "NOT_IMPLEMENTED",
        }

    def list_books(self):
        return {"books": self.catalogue.list_books(), "count": len(self.catalogue.list_books())}

    def check_readiness(self, book_id=None):
        graph_report = self.graph.verify()
        standards = rules_status(self.root)
        books = self.catalogue.list_books()
        if book_id:
            books = [book for book in books if book["id"] == book_id]
            if not books:
                raise ContractError("book %s is not in the catalogue" % book_id)
        decisions = []
        for book in books:
            blockers = []
            if book["readiness"] != "READY":
                blockers.append("CATALOGUE_%s" % book["readiness"])
            if standards["status"] != "AVAILABLE":
                blockers.append("BLOCKED_STANDARD")
            decisions.append({
                "book_id": book["id"],
                "catalogue_readiness": book["readiness"],
                "decision": "READY" if not blockers else "BLOCKED",
                "blockers": blockers,
            })
        return {
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

    def produce_next(self, dry_run=False):
        if not dry_run:
            raise NotImplementedStageError("Foundation PR1 supports produce-next only with --dry-run")
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
            "message": "Foundation PR1 does not execute production stages",
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
        return {
            "status": "PASS",
            "schemas": schemas,
            "worker_contracts": worker_contracts,
            "source_graph": {"passed": graph_report["passed"], "graph_hash": graph_report["graph_hash"]},
            "rules": rules_status(self.root),
            "note": "missing authoritative rules are a production blocker, not a schema-validation failure",
        }
