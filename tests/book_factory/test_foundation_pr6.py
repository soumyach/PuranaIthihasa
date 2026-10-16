import binascii
import copy
import json
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from book_factory.approvals import ApprovalStore
from book_factory.director import FactoryDirector
from book_factory.errors import BudgetExceededError, ContractError, ProviderUnavailableError
from book_factory.illustration_production import (
    MAX_ATTEMPTS_TOTAL,
    REVIEW_DIMENSIONS,
    ProofExecutionLedger,
    build_character_reference_registry,
    build_contact_sheet_svg,
    build_style_approval_request,
    discover_image_backends,
    finalize_visual_review,
    inspect_png,
    validate_proof_receipts,
)
from book_factory.providers.codex_image import CodexNativeImageProvider
from book_factory.source_graph import ReadOnlySourceGraph
from book_factory.util import content_hash, load_json, tree_snapshot
from book_factory.versioning import CharacterBibleVersionStore


ROOT = Path(__file__).resolve().parents[2]
BOOKS = ROOT / "books"


def png_bytes(width=1086, height=1448, rgb=(7, 31, 53)):
    def chunk(kind, payload):
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", binascii.crc32(kind + payload) & 0xFFFFFFFF)

    row = b"\x00" + bytes(rgb) * width
    pixels = row * height
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(pixels, 9))
        + chunk(b"IEND", b"")
    )


def request(proof_id="proof-a", attempt=1, estimate=0, paid=False):
    value = {
        "book_id": "DM04",
        "proof_id": proof_id,
        "attempt_number": attempt,
        "operation_key": content_hash([proof_id, attempt, estimate, paid]),
        "estimated_cost_minor_units": estimate,
        "paid_operation": paid,
    }
    value["request_hash"] = content_hash(value)
    return value


def receipt_for(path, proof_id="proof-a", color_index=0):
    image = inspect_png(path)
    return {
        "schema_version": "1.0",
        "book_id": "DM04",
        "proof_id": proof_id,
        "page_id": "page-%s" % proof_id,
        "generation_version": 1,
        "proof_spec_hash": content_hash([proof_id, "spec"]),
        "request_hash": content_hash([proof_id, "request"]),
        "character_reference_ids": ["character-reference-%d" % color_index],
        "image": dict(image, path=path.name),
        "estimated_cost_minor_units": 0,
        "actual_cost_minor_units": 0,
    }


def pass_review(receipt, reviewer_id="reviewer"):
    response = {
        "result": "PASS",
        "actual_pixels_inspected": True,
        "reviewer": {"id": reviewer_id},
        "dimension_assessments": [
            {"dimension": dimension, "result": "PASS", "findings": []}
            for dimension in REVIEW_DIMENSIONS
        ],
        "findings": [],
    }
    request_value = {
        "book_id": receipt["book_id"],
        "proof_id": receipt["proof_id"],
        "page_id": receipt["page_id"],
        "image": receipt["image"],
        "proof_spec_hash": receipt["proof_spec_hash"],
        "producer": {"id": "producer"},
        "request_hash": content_hash([receipt["proof_id"], "review"]),
    }
    response["request_hash"] = request_value["request_hash"]
    return request_value, response


class FoundationPR6AcceptanceTests(unittest.TestCase):
    def test_01_provider_availability_detection(self):
        self.assertEqual(discover_image_backends(environment={}, builtin_available=True)["selected_provider_id"], "codex-built-in-image-gen")
        self.assertIsNone(discover_image_backends(environment={}, builtin_available=False)["selected_provider_id"])
        provider = CodexNativeImageProvider()
        self.assertFalse(provider.capabilities()["available"])
        with self.assertRaises(ProviderUnavailableError):
            provider.generate({}, "op")

    def test_02_authenticated_provider_configuration(self):
        report = discover_image_backends(environment={"OPENAI_API_KEY": "present"}, builtin_available=False)
        api = next(item for item in report["candidates"] if item["provider_id"] == "openai-image-api")
        self.assertTrue(api["credential_available"])
        self.assertFalse(api["available"])
        self.assertIn("PAID_SPEND_NOT_AUTHORIZED", api["blockers"])

    def test_03_no_unauthorized_paid_calls(self):
        with tempfile.TemporaryDirectory() as temporary:
            ledger = ProofExecutionLedger(Path(temporary) / "books", "DM04")
            with self.assertRaises(BudgetExceededError):
                ledger.prepare(request(estimate=1, paid=True), {
                    "paid_calls_enabled": False, "job_max_minor_units": 0,
                })
            self.assertEqual(ledger.events(), [])

    def test_04_maximum_spending_enforcement(self):
        with tempfile.TemporaryDirectory() as temporary:
            ledger = ProofExecutionLedger(Path(temporary) / "books", "DM04")
            with self.assertRaises(BudgetExceededError):
                ledger.prepare(request(estimate=2, paid=True), {
                    "paid_calls_enabled": True, "job_max_minor_units": 1,
                })

    def test_05_two_attempt_and_total_attempt_limits(self):
        with tempfile.TemporaryDirectory() as temporary:
            ledger = ProofExecutionLedger(Path(temporary) / "books", "DM04")
            policy = {"paid_calls_enabled": False, "job_max_minor_units": 0}
            ledger.prepare(request("proof-a", 1), policy)
            ledger.prepare(request("proof-a", 2), policy)
            with self.assertRaises(ContractError):
                ledger.prepare(request("proof-a", 3), policy)
            for number in range(3):
                ledger.prepare(request("proof-%d" % number, 1), policy)
                ledger.prepare(request("proof-%d" % number, 2), policy)
            self.assertEqual(len([item for item in ledger.events() if item["status"] == "INTENT_RECORDED"]), MAX_ATTEMPTS_TOTAL)
            with self.assertRaises(ContractError):
                ledger.prepare(request("proof-z", 1), policy)

    def test_06_image_existence_integrity_and_hash_validation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            image = root / "proof.png"
            image.write_bytes(png_bytes())
            receipt = receipt_for(image)
            self.assertEqual(inspect_png(image)["integrity"], "PASS_CRC_AND_PIXEL_STREAM")
            self.assertEqual(validate_proof_receipts(root, [receipt])["result"], "PASS")
            receipt["image"]["sha256"] = "0" * 64
            self.assertIn("IMAGE_HASH_MISMATCH", {item["code"] for item in validate_proof_receipts(root, [receipt])["findings"]})

    def test_07_output_dimension_validation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            image = root / "wrong.png"
            image.write_bytes(png_bytes(300, 400))
            result = validate_proof_receipts(root, [receipt_for(image)])
            self.assertIn("IMAGE_DIMENSION_MISMATCH", {item["code"] for item in result["findings"]})

    def test_08_stable_character_reference_ids(self):
        record = CharacterBibleVersionStore(BOOKS).versions("DM04")[-1]
        first = build_character_reference_registry("DM04", record)
        second = build_character_reference_registry("DM04", record)
        self.assertEqual(first, second)
        self.assertEqual(len(first["entries"]), 45)
        self.assertEqual(
            [item["reference_id"] for item in first["entries"]],
            [item["reference_id"] for item in second["entries"]],
        )

    def test_09_approval_inheritance_restrictions(self):
        with tempfile.TemporaryDirectory() as temporary:
            store = ApprovalStore(temporary)
            digest = "a" * 64
            store.create(
                "CHARACTER_FAMILY", "CHARACTER_VARIANT", digest,
                {"type": "character_family", "id": "devi"},
                {"id": "human"}, {"id": "artist"}, "PASS",
                inheritance_allowed=True, source_scope="DM04",
                tradition_id="devi-mahatmya", edition_id="locked",
            )
            self.assertIsNone(store.find_valid(
                "CHARACTER_VARIANT", digest,
                {"type": "character_family", "id": "mahisha", "ancestors": ["devi"]},
                target_context={"source_scope": "DM04", "tradition_id": "devi-mahatmya", "edition_id": "other"},
            ))

    def test_10_image_review_independence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            image = root / "proof.png"
            image.write_bytes(png_bytes())
            receipt = receipt_for(image)
            review_request, response = pass_review(receipt, reviewer_id="producer")
            with self.assertRaises(ContractError):
                finalize_visual_review(review_request, response, root)

    def test_11_no_false_visual_pass(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            image = root / "proof.png"
            image.write_bytes(png_bytes())
            review_request, response = pass_review(receipt_for(image))
            response["dimension_assessments"][0]["result"] = "FIX"
            with self.assertRaises(ContractError):
                finalize_visual_review(review_request, response, root)

    def test_12_approved_image_binding_is_immutable(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            image = root / "proof.png"
            image.write_bytes(png_bytes())
            receipt = receipt_for(image)
            review_request, response = pass_review(receipt)
            review = finalize_visual_review(review_request, response, root)
            approval = build_style_approval_request(
                "DM04", [receipt], [review], "b" * 64, "c" * 64,
                {"graph": "d" * 64}, {"contact_sheet_hash": "e" * 64},
            )
            self.assertEqual(approval["assets"][0]["image_hash"], receipt["image"]["sha256"])
            mutated = copy.deepcopy(receipt)
            mutated["image"]["sha256"] = "f" * 64
            changed = build_style_approval_request(
                "DM04", [mutated], [], "b" * 64, "c" * 64,
                {"graph": "d" * 64}, {"contact_sheet_hash": "e" * 64},
            )
            self.assertNotEqual(approval["approval_request_hash"], changed["approval_request_hash"])

    def test_13_idempotent_retry_and_resume(self):
        with tempfile.TemporaryDirectory() as temporary:
            ledger = ProofExecutionLedger(Path(temporary) / "books", "DM04")
            value = request()
            policy = {"paid_calls_enabled": False, "job_max_minor_units": 0}
            first = ledger.prepare(value, policy)
            second = ledger.prepare(value, policy)
            self.assertFalse(first["idempotent"])
            self.assertTrue(second["idempotent"])
            self.assertEqual(len(ledger.events()), 1)

    def test_14_contact_sheet_completeness(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            receipts = []
            reviews = []
            for number, color in enumerate(((7, 31, 53), (216, 172, 78), (105, 32, 25), (37, 28, 24)), 1):
                image = root / ("proof-%d.png" % number)
                image.write_bytes(png_bytes(rgb=color))
                receipt = receipt_for(image, "proof-%d" % number, number)
                review_request, response = pass_review(receipt, "reviewer")
                receipts.append(receipt)
                reviews.append(finalize_visual_review(review_request, response, root))
            destination = root / "contact.svg"
            metadata = build_contact_sheet_svg(root, receipts, reviews, destination)
            self.assertEqual(len(metadata["proofs"]), 4)
            self.assertEqual({item["visual_qa_status"] for item in metadata["proofs"]}, {"PASS"})
            text = destination.read_text(encoding="utf-8")
            self.assertEqual(text.count("data:image/png;base64,"), 4)

    def test_15_source_graph_read_only_protection(self):
        graph_root = ROOT / "research" / "source-graph"
        before = tree_snapshot(graph_root)
        self.assertTrue(ReadOnlySourceGraph(graph_root).verify()["passed"])
        self.assertEqual(before, tree_snapshot(graph_root))

    def test_16_prior_factory_validation_remains_available(self):
        result = FactoryDirector(ROOT).validate()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["source_graph"]["graph_hash"], "f3a02b5eebbe4b11035240f64ede32fcf889ff7b85f481dfe11b13744a0fc6b1")


if __name__ == "__main__":
    unittest.main()
