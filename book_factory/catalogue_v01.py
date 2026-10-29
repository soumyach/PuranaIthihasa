"""Lossless adapter for the authoritative Illustrated Library catalogue v0.1."""

from copy import deepcopy
from pathlib import Path

from .errors import ContractError
from .util import load_json, sha256_bytes


EXPECTED_CATALOGUE_SHA256 = "e80483a0c77e8453616868b85ce883407e7c5bfaa81fae5d6c605266764c2f5b"
PRIORITY_ORDER = {
    "P0": 10,
    "P0-COMPANION": 20,
    "P0/P1": 30,
    "P1": 40,
    "P1-RESEARCH": 50,
    "FUTURE": 80,
    "FUTURE-IP": 90,
}


class SourceMappingRegistry:
    """Reviewed catalogue-to-graph bindings; absence remains explicit."""

    def __init__(self, path):
        self.path = Path(path)
        self.data = load_json(self.path)

    def resolve(self, book_id):
        mapping = deepcopy(self.data.get("mappings", {}).get(book_id))
        if mapping is None:
            return {"outcome": self.data["policy"]["unlisted_outcome"], "segments": []}
        return mapping

    def pilot_ranking(self):
        return deepcopy(self.data.get("pilot_ranking", []))


def import_authoritative_v01(source, mapping_registry, expected_hash=EXPECTED_CATALOGUE_SHA256):
    """Normalize for the factory without discarding or overwriting original fields."""

    source = Path(source)
    payload = source.read_bytes()
    actual_hash = sha256_bytes(payload)
    if actual_hash != expected_hash:
        raise ContractError("authoritative catalogue hash mismatch", {"expected": expected_hash, "actual": actual_hash})
    raw = load_json(source)
    if not isinstance(raw.get("collections"), dict) or not isinstance(raw.get("books"), list):
        raise ContractError("authoritative v0.1 catalogue has an unexpected shape")
    if raw.get("counts", {}).get("total") != len(raw["books"]):
        raise ContractError("authoritative catalogue total does not match its books")

    collections = []
    for code, original in raw["collections"].items():
        item = deepcopy(original)
        item["id"] = code
        item["code"] = code
        item["original"] = deepcopy(original)
        collections.append(item)

    books = []
    for original in raw["books"]:
        item = deepcopy(original)
        book_id = item["id"]
        collection = item["collection"]
        if collection not in raw["collections"]:
            raise ContractError("%s references an unknown original collection" % book_id)
        mapping = mapping_registry.resolve(book_id)
        spine_ids = []
        for segment in mapping.get("segments", []):
            if segment["story_spine_id"] not in spine_ids:
                spine_ids.append(segment["story_spine_id"])
        original_graph_status = item["graph_readiness"]
        source_status = (
            "INCOMPLETE_SOURCE"
            if mapping["outcome"] in {"VERIFIED_EXACT", "VERIFIED_SUBSET"}
            else "NEEDS_SOURCE_REVIEW"
        )
        if original_graph_status == "ORIGINAL_FICTION":
            source_status = "NEEDS_SOURCE_REVIEW"
        edition_status = "EXISTING_EDITION" if book_id == "DM08" else "PLANNED"
        automatic = book_id != "DM08"
        item.update({
            "collection_ids": [collection],
            "line": "ORIGINALS_KALPANA" if collection == "KAL" else "KATHAS",
            "source_class": "KALPANA" if collection == "KAL" else "MULA",
            "priority": PRIORITY_ORDER.get(raw["collections"][collection].get("priority"), 100),
            "readiness": source_status,
            "story_spine_ids": spine_ids,
            "source_mapping": mapping,
            "rights_status": "UNKNOWN",
            "edition_status": edition_status,
            "automatic_production_eligible": automatic,
            "publication_readiness_status": "PENDING_INDEPENDENT_REVIEW" if book_id == "DM08" else "NOT_ASSESSED",
            "source_verification_status": "PENDING_SCOPE_RECONCILIATION" if book_id == "DM08" else source_status,
            "factory": {
                "mapping": deepcopy(mapping),
                "edition_status": edition_status,
                "automatic_production_eligible": automatic,
                "publication_readiness_status": "PENDING_INDEPENDENT_REVIEW" if book_id == "DM08" else "NOT_ASSESSED",
                "source_verification_status": "PENDING_SCOPE_RECONCILIATION" if book_id == "DM08" else source_status,
                "rights_status": "UNKNOWN",
            },
            "original": deepcopy(original),
        })
        books.append(item)

    normalized = {
        "schema_version": "1.0",
        "metadata": {
            "title": raw["title"],
            "created": raw["created"],
            "status": raw["status"],
            "method": raw["method"],
            "reference_book": raw["reference_book"],
            "counts": deepcopy(raw["counts"]),
            "source_path": source.name,
            "source_sha256": actual_hash,
            "normalization": "LOSSLESS_V01_WITH_NAMESPACED_FACTORY_DERIVATIONS",
        },
        "collections": collections,
        "books": books,
    }
    return normalized
