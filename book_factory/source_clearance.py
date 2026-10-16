"""Evidence-bound clearance for private drafting; never a publication licence."""

from pathlib import Path

from .errors import ContractError
from .util import atomic_json_write, content_hash, load_json, stable_id


PRIVATE_DRAFT_OPEN = "PRIVATE_DRAFT_PERMITTED_PUBLICATION_BLOCKED"


def finalize_clearance(record):
    """Add deterministic identity fields to a complete clearance record."""
    unsigned = {key: value for key, value in record.items() if key not in {"clearance_hash", "id"}}
    digest = content_hash(unsigned)
    result = dict(unsigned)
    result["clearance_hash"] = digest
    result["id"] = stable_id("source-clearance", result["book_id"], digest)
    return result


def validate_private_draft_clearance(record, dossier, packets):
    if record.get("book_id") != dossier.get("book_id"):
        raise ContractError("source clearance and dossier book ids differ")
    if record.get("dossier_hash") != dossier.get("dossier_hash"):
        raise ContractError("source clearance does not bind the active dossier")
    expected_packets = sorted(packet["packet_hash"] for packet in packets)
    if sorted(record.get("packet_hashes", [])) != expected_packets:
        raise ContractError("source clearance does not bind the active Story Packet set")
    if record.get("graph_hash") != dossier.get("graph_hash"):
        raise ContractError("source clearance graph hash is stale")
    if record.get("private_draft_gate") != PRIVATE_DRAFT_OPEN:
        raise ContractError("private manuscript drafting is not cleared")
    rights = record.get("rights_determination", {})
    if rights.get("use") != "ORIGINAL_ENGLISH_ADAPTATION_FROM_EVIDENCE_PARAPHRASES":
        raise ContractError("clearance does not permit the requested adaptation use")
    if rights.get("modern_web_presentation_reuse") != "PROHIBITED":
        raise ContractError("modern website presentation reuse must remain prohibited")
    review = record.get("independent_source_review", {})
    if not review.get("executed") or not review.get("reviewer_id"):
        raise ContractError("an executed independent source review is required")
    if review.get("result") not in {"PASS_FOR_PRIVATE_DRAFT", "PASS_WITH_LIMITATIONS"}:
        raise ContractError("independent source review did not clear a private draft")
    if record.get("publication_gate") != "BLOCKED":
        raise ContractError("PR4 source clearance may not open publication")
    return record


class SourceClearanceStore:
    def __init__(self, books_root):
        self.books_root = Path(books_root)

    def _root(self, book_id):
        return self.books_root / book_id / "source-clearance"

    def put(self, record):
        finalized = finalize_clearance(record)
        if record.get("clearance_hash") and record["clearance_hash"] != finalized["clearance_hash"]:
            raise ContractError("source clearance hash does not match content")
        if record.get("id") and record["id"] != finalized["id"]:
            raise ContractError("source clearance id does not match content")
        path = self._root(finalized["book_id"]) / (finalized["clearance_hash"] + ".json")
        if path.exists() and load_json(path) != finalized:
            raise ContractError("source clearance hash collision")
        if not path.exists():
            atomic_json_write(path, finalized)
        return finalized, path

    def records(self, book_id):
        return [load_json(path) for path in sorted(self._root(book_id).glob("*.json"))]

    def latest(self, book_id):
        records = self.records(book_id)
        if not records:
            raise ContractError("no source clearance is recorded for %s" % book_id)
        return records[-1]
