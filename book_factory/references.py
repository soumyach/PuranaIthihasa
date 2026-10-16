"""Validation for immutable reference editions and optional local binaries."""

from pathlib import Path

from .contracts import validate_named
from .errors import ContractError
from .util import load_json, sha256_bytes


class ReferenceEditionRegistry:
    def __init__(self, repository_root):
        self.root = Path(repository_root)

    def load(self, book_id):
        path = self.root / "book-factory" / "references" / "editions" / (book_id + ".json")
        record = load_json(path)
        validate_named(record, self.root / "schemas" / "book-factory", "reference-edition")
        return record

    def verify(self, book_id):
        record = self.load(book_id)
        assets = []
        for item in record["assets"]:
            path = self.root / item["path"]
            if not path.is_file():
                if item["storage_mode"] == "LOCAL_UNTRACKED_REFERENCE":
                    assets.append({"asset_id": item["asset_id"], "availability": "MISSING_LOCAL_REFERENCE", "sha256": item["sha256"]})
                    continue
                raise ContractError("tracked reference asset is missing", {"path": item["path"]})
            actual = sha256_bytes(path.read_bytes())
            if actual != item["sha256"]:
                raise ContractError("reference edition asset hash mismatch", {"path": item["path"], "actual": actual})
            assets.append({"asset_id": item["asset_id"], "availability": "AVAILABLE", "sha256": actual})
        return {"book_id": book_id, "edition_status": record["edition_status"], "assets": assets}
