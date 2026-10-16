"""Versioned catalogue storage and deterministic production selection."""

from copy import deepcopy
from pathlib import Path

from .errors import ContractError
from .util import atomic_json_write, load_json


READINESS_STATES = {
    "READY",
    "NEEDS_SOURCE_REVIEW",
    "INCOMPLETE_SOURCE",
    "BLOCKED",
    "COMPLETED",
}


def validate_catalogue(catalogue):
    if not isinstance(catalogue, dict) or not isinstance(catalogue.get("books"), list):
        raise ContractError("catalogue must be an object with a books array")
    collections = catalogue.get("collections", [])
    if not isinstance(collections, list):
        raise ContractError("catalogue collections must be an array")
    collection_ids = [item.get("id") for item in collections]
    if any(not isinstance(item, str) or not item for item in collection_ids):
        raise ContractError("every collection requires a non-empty id")
    if len(collection_ids) != len(set(collection_ids)):
        raise ContractError("collection ids must be unique")
    book_ids = []
    for book in catalogue["books"]:
        book_id = book.get("id")
        if not isinstance(book_id, str) or not book_id:
            raise ContractError("every book requires its original non-empty id")
        book_ids.append(book_id)
        if book.get("readiness") not in READINESS_STATES:
            raise ContractError("%s has invalid readiness" % book_id)
        relationships = book.get("collection_ids", [])
        if not isinstance(relationships, list) or not set(relationships).issubset(set(collection_ids)):
            raise ContractError("%s references an unknown collection" % book_id)
        if book.get("line") not in {"KATHAS", "ORIGINALS_KALPANA"}:
            raise ContractError("%s has invalid product line" % book_id)
        if book.get("line") == "ORIGINALS_KALPANA" and book.get("source_class") != "KALPANA":
            raise ContractError("%s must be explicitly classified KALPANA" % book_id)
    if len(book_ids) != len(set(book_ids)):
        raise ContractError("book ids must be unique")
    return catalogue


class CatalogueStore:
    def __init__(self, path):
        self.path = Path(path)

    def load(self):
        return validate_catalogue(load_json(self.path))

    def import_file(self, source, dry_run=False):
        incoming = validate_catalogue(load_json(source))
        current = self.load() if self.path.exists() else {"schema_version": "1.0", "collections": [], "books": []}
        collections = {item["id"]: deepcopy(item) for item in current.get("collections", [])}
        for item in incoming.get("collections", []):
            existing = collections.get(item["id"])
            if existing is not None and existing != item:
                raise ContractError("collection id %s already exists with different data" % item["id"])
            collections[item["id"]] = deepcopy(item)
        books = {item["id"]: deepcopy(item) for item in current["books"]}
        for item in incoming["books"]:
            existing = books.get(item["id"])
            if existing is not None and existing != item:
                raise ContractError("book id %s already exists with different data" % item["id"])
            books[item["id"]] = deepcopy(item)
        merged = {
            "schema_version": "1.0",
            "collections": sorted(collections.values(), key=lambda item: item["id"]),
            "books": sorted(books.values(), key=lambda item: item["id"]),
        }
        validate_catalogue(merged)
        if not dry_run:
            atomic_json_write(self.path, merged)
        return merged

    def list_books(self):
        return sorted(self.load()["books"], key=lambda item: item["id"])

    def get(self, book_id):
        return next((book for book in self.load()["books"] if book["id"] == book_id), None)

    def select_next(self, active_book_ids=None):
        excluded = set(active_book_ids or [])
        ready = [
            book
            for book in self.load()["books"]
            if book["readiness"] == "READY" and book["id"] not in excluded
        ]
        ready.sort(key=lambda item: (item.get("priority", 1000), item["id"]))
        return ready[0] if ready else None
