"""Immutable, parent-linked versions for manuscripts and semantic reviews."""

from pathlib import Path

from .errors import ContractError
from .util import atomic_json_write, content_hash, load_json, stable_id


class ImmutableVersionStore:
    def __init__(self, books_root, kind):
        self.books_root = Path(books_root)
        self.kind = kind

    def _root(self, book_id):
        return self.books_root / book_id / self.kind

    def versions(self, book_id):
        root = self._root(book_id)
        records = sorted(
            (load_json(path) for path in root.glob("v[0-9][0-9][0-9][0-9].json")),
            key=lambda item: item["version"],
        )
        parent_hash = None
        for expected_version, record in enumerate(records, 1):
            if record.get("version") != expected_version:
                raise ContractError("immutable version sequence is not contiguous")
            if record.get("book_id") != book_id or record.get("kind") != self.kind:
                raise ContractError("immutable version identity does not match its store")
            if record.get("parent_hash") != parent_hash:
                raise ContractError("immutable version parent chain is broken")
            unsigned = {key: value for key, value in record.items() if key not in {"content_hash", "id"}}
            digest = content_hash(unsigned)
            if record.get("content_hash") != digest:
                raise ContractError("immutable version content hash is invalid")
            if record.get("id") != stable_id(self.kind, book_id, digest):
                raise ContractError("immutable version id is invalid")
            parent_hash = digest
        return records

    def put(self, book_id, payload, parent_hash=None):
        current = self.versions(book_id)
        for record in current:
            if record["payload"] == payload and record.get("parent_hash") == parent_hash:
                return record
        expected_version = len(current) + 1
        if current and parent_hash != current[-1]["content_hash"]:
            raise ContractError("new version must link to the latest immutable parent")
        if not current and parent_hash is not None:
            raise ContractError("first version cannot have a parent")
        unsigned = {
            "schema_version": "1.0",
            "book_id": book_id,
            "kind": self.kind,
            "version": expected_version,
            "parent_hash": parent_hash,
            "payload": payload,
        }
        digest = content_hash(unsigned)
        record = dict(unsigned, content_hash=digest, id=stable_id(self.kind, book_id, digest))
        path = self._root(book_id) / ("v%04d.json" % expected_version)
        if path.exists():
            existing = load_json(path)
            if existing != record:
                raise ContractError("immutable version already exists with different content")
            return existing
        atomic_json_write(path, record)
        return record


class ManuscriptVersionStore(ImmutableVersionStore):
    def __init__(self, books_root):
        super().__init__(books_root, "manuscripts")


class EditorialReviewStore(ImmutableVersionStore):
    def __init__(self, books_root):
        super().__init__(books_root, "editorial-reviews")
