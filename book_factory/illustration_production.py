"""PR6 illustration-proof production, validation, review, and approval gates.

The Codex built-in image tool is session-scoped and cannot be invoked by this
repository.  This module therefore implements an executable, auditable bridge:
the Director persists a locked request and zero-cost authorization before the
session tool runs, then imports and validates the real pixels and receipt.
"""

import base64
import binascii
import html
import json
import os
import shutil
import struct
import subprocess
import zlib
from copy import deepcopy
from pathlib import Path

from .errors import BudgetExceededError, ContractError, ProviderUnavailableError
from .util import (
    append_jsonl,
    atomic_json_write,
    atomic_write,
    content_hash,
    load_json,
    sha256_bytes,
    stable_id,
    utc_now,
)
from .versioning import (
    CharacterReferenceVersionStore,
    IllustrationProofVersionStore,
    StyleApprovalRequestVersionStore,
    VisualReviewVersionStore,
)


TARGET_CANVAS = {"aspect_ratio": "3:4", "pixel_width": 1086, "pixel_height": 1448}
MAX_ATTEMPTS_PER_PROOF = 2
MAX_ATTEMPTS_TOTAL = 8
MAX_GIT_ASSET_BYTES = 100 * 1024 * 1024
REVIEW_RESULTS = {"PASS", "FIX", "ESCALATE"}
REVIEW_DIMENSIONS = (
    "source_fidelity",
    "religious_iconography",
    "character_identity",
    "limbs",
    "weapons_and_mounts",
    "anatomy",
    "composition",
    "environmental_consistency",
    "cropping_and_clipping",
    "lighting_and_color",
    "series_identity",
    "scripted_page_suitability",
    "lettering_safe_regions",
)
PRIORITY_CHARACTER_IDS = {
    "dm-devi", "dm-mahisha", "dm-lion", "dm-medhas", "dm-suratha", "dm-samadhi",
    "dm-gods", "dm-asura-army", "dm-chikshura", "dm-chamara",
}


def discover_image_backends(environment=None, local_tools=None, builtin_available=True):
    """Return capability facts without reading or exposing credential values."""
    environment = environment if environment is not None else os.environ
    local_tools = set(local_tools or [])
    candidates = [
        {
            "provider_id": "codex-built-in-image-gen",
            "provider": "Codex built-in image generation",
            "model": "NOT_SURFACED_BY_BUILTIN_TOOL",
            "operations": ["generate", "edit", "reference_conditioning"],
            "reference_conditioning": True,
            "native_output_dimensions": "PROVIDER_SELECTED; VALIDATE AFTER GENERATION",
            "target_handling": "CONTROLLED_CROP_AND_RESAMPLE_TO_1086x1448_WITHOUT_STRETCH",
            "cost_per_operation": "NO_DIRECT_MONETARY_PRICE_EXPOSED_TO_REPOSITORY",
            "estimated_total_proof_cost_minor_units": 0,
            "currency": "USD",
            "credential": "NO_OPENAI_API_KEY_REQUIRED",
            "credential_available": True,
            "usage_limits": "ACCOUNT_OR_SESSION_LIMITS_NOT_SURFACED_TO_REPOSITORY",
            "integration": "CODEX_NATIVE_IMAGE_TOOL_SESSION_HANDOFF",
            "available": bool(builtin_available),
            "actual_creation_executable": bool(builtin_available),
            "billable_repository_call": False,
        },
        {
            "provider_id": "openai-image-api",
            "provider": "OpenAI Image API",
            "model": "gpt-image-2",
            "operations": ["generate", "edit", "reference_conditioning"],
            "reference_conditioning": True,
            "native_output_dimensions": "API_CONFIGURABLE_WITHIN_MODEL_LIMITS",
            "target_handling": "EXACT_OR_CONTROLLED_CROP_AND_RESAMPLE",
            "cost_per_operation": "BILLABLE; LIVE PRICE NOT PINNED IN REPOSITORY",
            "estimated_total_proof_cost_minor_units": None,
            "currency": "USD",
            "credential": "OPENAI_API_KEY",
            "credential_available": bool(environment.get("OPENAI_API_KEY")),
            "usage_limits": "ACCOUNT_SPECIFIC_AND_NOT_AVAILABLE_OFFLINE",
            "integration": "EXPLICIT_CLI_FALLBACK_ONLY_AFTER_USER_CONFIRMATION",
            "available": False,
            "actual_creation_executable": False,
            "billable_repository_call": True,
            "blockers": ["CREDENTIAL_ABSENT" if not environment.get("OPENAI_API_KEY") else "PAID_SPEND_NOT_AUTHORIZED"],
        },
        {
            "provider_id": "authorized-local-image-runtime",
            "provider": "Authorized local diffusion runtime",
            "model": "NOT_CONFIGURED",
            "operations": ["generate", "edit", "reference_conditioning"],
            "reference_conditioning": "RUNTIME_DEPENDENT",
            "native_output_dimensions": "RUNTIME_DEPENDENT",
            "target_handling": "RUNTIME_DEPENDENT",
            "cost_per_operation": "LOCAL_COMPUTE_ONLY_IF_CONFIGURED",
            "estimated_total_proof_cost_minor_units": 0,
            "currency": "USD",
            "credential": "LOCAL_RUNTIME",
            "credential_available": bool(local_tools),
            "usage_limits": "LOCAL_HARDWARE_DEPENDENT",
            "integration": "LOCAL_EXECUTABLE_ADAPTER",
            "available": bool(local_tools),
            "actual_creation_executable": bool(local_tools),
            "billable_repository_call": False,
            "detected_tools": sorted(local_tools),
        },
    ]
    selected = "codex-built-in-image-gen" if builtin_available else None
    result = {
        "schema_version": "1.0",
        "selected_provider_id": selected,
        "selection_reason": (
            "Only supported zero-direct-cost backend available in the current Codex session."
            if selected else "No authorized executable image backend is available."
        ),
        "candidates": candidates,
    }
    result["capability_hash"] = content_hash(result)
    return result


def _png_chunks(payload):
    if not payload.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ContractError("proof image is not a PNG")
    offset = 8
    chunks = []
    while offset < len(payload):
        if offset + 12 > len(payload):
            raise ContractError("PNG is truncated")
        length = struct.unpack(">I", payload[offset:offset + 4])[0]
        kind = payload[offset + 4:offset + 8]
        data_start = offset + 8
        data_end = data_start + length
        crc_end = data_end + 4
        if crc_end > len(payload):
            raise ContractError("PNG chunk is truncated")
        data = payload[data_start:data_end]
        expected_crc = struct.unpack(">I", payload[data_end:crc_end])[0]
        actual_crc = binascii.crc32(kind + data) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            raise ContractError("PNG chunk CRC is invalid")
        chunks.append((kind, data))
        offset = crc_end
        if kind == b"IEND":
            if offset != len(payload):
                raise ContractError("PNG has trailing bytes")
            break
    if not chunks or chunks[0][0] != b"IHDR" or chunks[-1][0] != b"IEND":
        raise ContractError("PNG structure is incomplete")
    return chunks


def inspect_png(path):
    path = Path(path)
    if not path.is_file():
        raise ContractError("proof image does not exist", {"path": str(path)})
    payload = path.read_bytes()
    if not payload or len(payload) > MAX_GIT_ASSET_BYTES:
        raise ContractError("proof image is empty or exceeds normal Git size policy")
    chunks = _png_chunks(payload)
    ihdr = chunks[0][1]
    if len(ihdr) != 13:
        raise ContractError("PNG IHDR is invalid")
    width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(">IIBBBBB", ihdr)
    if width < 1 or height < 1 or compression != 0 or filtering != 0:
        raise ContractError("PNG dimensions or encoding method are invalid")
    compressed = b"".join(data for kind, data in chunks if kind == b"IDAT")
    try:
        decoded = zlib.decompress(compressed)
    except zlib.error as exc:
        raise ContractError("PNG pixel stream is unreadable", {"reason": str(exc)})
    if not decoded:
        raise ContractError("PNG contains no readable pixels")
    if interlace == 0:
        channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(color_type)
        if channels is None or bit_depth not in {1, 2, 4, 8, 16}:
            raise ContractError("PNG pixel format is unsupported")
        row_bytes = (width * channels * bit_depth + 7) // 8
        if len(decoded) != (row_bytes + 1) * height:
            raise ContractError("PNG pixel stream length is invalid")
    return {
        "format": "PNG",
        "width": width,
        "height": height,
        "aspect_ratio": "%d:%d" % _reduced_ratio(width, height),
        "sha256": sha256_bytes(payload),
        "bytes": len(payload),
        "readable": True,
        "integrity": "PASS_CRC_AND_PIXEL_STREAM",
    }


def _reduced_ratio(width, height):
    import math

    divisor = math.gcd(width, height)
    return width // divisor, height // divisor


def normalize_to_canvas(source_path, destination_path):
    """Normalize by center-cropping to 3:4, then resizing; never stretch."""
    source_path = Path(source_path)
    destination_path = Path(destination_path)
    info = inspect_png(source_path)
    if info["width"] == TARGET_CANVAS["pixel_width"] and info["height"] == TARGET_CANVAS["pixel_height"]:
        atomic_write(destination_path, source_path.read_bytes())
        return {"method": "IDENTITY_COPY", "source": info, "crop": None, "output": inspect_png(destination_path)}
    sips = shutil.which("sips")
    if not sips:
        raise ContractError("non-target PNG requires the authorized sips framing tool")
    width, height = info["width"], info["height"]
    if width * 4 > height * 3:
        crop_height = height - (height % 4)
        crop_width = crop_height * 3 // 4
    else:
        crop_width = width - (width % 3)
        crop_height = crop_width * 4 // 3
    if crop_width < 3 or crop_height < 4:
        raise ContractError("image is too small for controlled 3:4 framing")
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination_path.with_name(".%s.crop.png" % destination_path.stem)
    try:
        crop = subprocess.run(
            [sips, "--cropToHeightWidth", str(crop_height), str(crop_width), str(source_path), "--out", str(temporary)],
            capture_output=True, text=True, check=False,
        )
        if crop.returncode:
            raise ContractError("controlled image crop failed", {"stderr": crop.stderr.strip()})
        resize = subprocess.run(
            [sips, "--resampleHeightWidth", str(TARGET_CANVAS["pixel_height"]), str(TARGET_CANVAS["pixel_width"]), str(temporary), "--out", str(destination_path)],
            capture_output=True, text=True, check=False,
        )
        if resize.returncode:
            raise ContractError("controlled image resize failed", {"stderr": resize.stderr.strip()})
    finally:
        if temporary.exists():
            temporary.unlink()
    output = inspect_png(destination_path)
    if (output["width"], output["height"]) != (TARGET_CANVAS["pixel_width"], TARGET_CANVAS["pixel_height"]):
        raise ContractError("normalized proof does not match the locked canvas")
    return {
        "method": "CENTER_CROP_THEN_RESAMPLE_NO_STRETCH",
        "source": info,
        "crop": {"width": crop_width, "height": crop_height},
        "output": output,
    }


def build_character_reference_registry(book_id, character_bible_record, approved_references=None):
    approved_references = approved_references or {}
    bible_hash = character_bible_record["content_hash"]
    entries = []
    for item in character_bible_record["payload"]["entries"]:
        character_id = item["id"]
        bound = list(approved_references.get(character_id, []))
        for reference in bound:
            if reference.get("approval_status") != "HUMAN_APPROVED_EXACT_ASSET":
                raise ContractError("character reference image requires exact human approval")
            if not reference.get("image_hash") or not reference.get("approval_id"):
                raise ContractError("approved character reference binding is incomplete")
        entry = {
            "reference_id": stable_id("character-reference", book_id, character_id, bible_hash),
            "canonical_character_id": character_id,
            "name": item["name"],
            "priority": character_id in PRIORITY_CHARACTER_IDS,
            "textual_facts": {
                "authoritative_source_record": item["authoritative_source_record"],
                "source_scope": item["source_scope"],
                "evidence_ids": item["evidence_ids"],
                "required_attributes": item["required_attributes"],
                "manifestation_rules": item["manifestation_rules"],
                "authorized_weapon_ids": item["authorized_weapon_ids"],
            },
            "approved_artistic_choices": {
                "proposed_visual_interpretation": item["proposed_visual_interpretation"],
                "visual_constants": item["visual_constants"],
                "clothing_policy": item["clothing_policy"],
                "ornament_policy": item["ornament_policy"],
                "silhouette_policy": item["silhouette_policy"],
                "arm_count_policy": item["arm_count_policy"],
                "allowed_artistic_choices": item["allowed_artistic_choices"],
            },
            "forbidden_attributes": sorted(set(item["prohibited_attributes"] + item["forbidden_iconographic_assumptions"])),
            "continuity_constraints": item["continuity_checks"],
            "approved_visual_references": bound,
            "reference_conditioning_status": "AVAILABLE" if bound else "TEXT_ONLY_PENDING_STYLE_APPROVAL",
        }
        entries.append(entry)
    payload = {
        "schema_version": "1.0",
        "book_id": book_id,
        "character_bible_hash": bible_hash,
        "binding_policy": "Only exact human-approved proof assets may become reusable image references.",
        "backend_limitation": "Built-in reference conditioning is available, but identity consistency still requires independent pixel review.",
        "entries": entries,
    }
    payload["registry_hash"] = content_hash(payload)
    return payload


def _prompt_value(value):
    if isinstance(value, str):
        return value
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def build_generation_request(book_id, proof_spec, page, character_registry, location_entry,
                             capability, proof_package_hash, manuscript_hash, rules_hash,
                             attempt_number, existing_reference_paths=None,
                             prior_visual_review_hash=None, revision_findings=None):
    if attempt_number not in {1, 2}:
        raise ContractError("proof attempt number must be one or two")
    references = {
        entry["canonical_character_id"]: entry
        for entry in character_registry["entries"] if entry["canonical_character_id"] in proof_spec["character_ids"]
    }
    if set(proof_spec["character_ids"]) - set(references):
        raise ContractError("proof references an unknown character")
    reference_paths = sorted(set(existing_reference_paths or []))
    revision_findings = [str(item).strip() for item in (revision_findings or []) if str(item).strip()]
    if attempt_number == 1 and (prior_visual_review_hash or revision_findings):
        raise ContractError("first proof attempt cannot claim prior review corrections")
    if attempt_number == 2 and (not prior_visual_review_hash or not revision_findings):
        raise ContractError("second proof attempt requires exact prior review findings")
    text_facts = [
        "%s: %s" % (entry["name"], entry["textual_facts"]["authoritative_source_record"]["source_facts"])
        for entry in references.values()
    ]
    visual_choices = [
        "%s: %s" % (
            entry["name"],
            entry["approved_artistic_choices"]["proposed_visual_interpretation"]["design_proposal"],
        ) for entry in references.values()
    ]
    forbidden = sorted({
        value for entry in references.values() for value in entry["forbidden_attributes"]
    } | set(proof_spec["exclusions"]))
    prompt_lines = [
        "Use case: illustration-story",
        "Asset type: Khatakshetra DM04 internal illustration proof; artwork only, no lettering",
        "Primary request: %s" % proof_spec["title"],
        "Scene/backdrop: %s. %s" % (location_entry["name"], location_entry["proposed_visual_interpretation"]["design_proposal"]),
        "Subject and sourced action: %s" % " ".join(page["narrative_beats"]),
        "Source-bounded character facts: %s" % " | ".join(text_facts),
        "Approved artistic proposals, not textual facts: %s" % " | ".join(visual_choices),
        "Style/medium: traditional Indian miniature and Kalamkari influences; rich painterly detail; devotional, dignified premium storybook atmosphere; expressive characters; jewel-toned scene colors; consistent navy and antique-gold ornamental framing cues",
        "Composition/framing: portrait 3:4; %s; protect the specified lettering-safe region with uncluttered negative space" % proof_spec["composition"],
        "Lighting/mood: %s" % location_entry["lighting"],
        "Color palette: midnight navy and antique gold anchors with saffron, vermilion, crimson, emerald, turquoise, peacock blue, royal purple, ivory and bronze inside the painting",
        "Constraints: %s" % " | ".join(proof_spec["source_boundaries"]),
        "Avoid: %s" % " | ".join(forbidden + ["generic Western fantasy armor", "futuristic elements", "speech balloons", "captions", "letters", "words", "watermarks"]),
    ]
    if revision_findings:
        prompt_lines.append(
            "Targeted attempt-2 corrections from independent pixel review: %s"
            % " | ".join(revision_findings)
        )
    unsigned = {
        "schema_version": "1.0",
        "book_id": book_id,
        "proof_id": proof_spec["id"],
        "proof_kind": proof_spec["kind"],
        "page_id": page["page_id"],
        "page_number": page["page_number"],
        "attempt_number": attempt_number,
        "operation": "generate",
        "provider_id": capability["provider_id"],
        "model": capability["model"],
        "integration": capability["integration"],
        "target_canvas": TARGET_CANVAS,
        "proof_spec_hash": content_hash(proof_spec),
        "proof_package_hash": proof_package_hash,
        "manuscript_hash": manuscript_hash,
        "rules_hash": rules_hash,
        "character_registry_hash": character_registry["registry_hash"],
        "character_reference_ids": sorted(entry["reference_id"] for entry in references.values()),
        "reference_image_paths": reference_paths,
        "prior_visual_review_hash": prior_visual_review_hash,
        "revision_findings": revision_findings,
        "source_support": proof_spec["source_support"],
        "safe_regions": proof_spec["safe_regions"],
        "prompt": "\n".join(prompt_lines),
        "estimated_cost_minor_units": 0,
        "currency": "USD",
        "paid_operation": False,
        "attempt_ceiling": MAX_ATTEMPTS_PER_PROOF,
        "book_attempt_ceiling": MAX_ATTEMPTS_TOTAL,
    }
    unsigned["operation_key"] = content_hash({
        "book_id": book_id,
        "proof_id": proof_spec["id"],
        "attempt_number": attempt_number,
        "proof_spec_hash": unsigned["proof_spec_hash"],
        "provider_id": unsigned["provider_id"],
        "prompt": unsigned["prompt"],
        "reference_image_paths": reference_paths,
    })
    unsigned["request_hash"] = content_hash(unsigned)
    return unsigned


class ProofExecutionLedger:
    def __init__(self, books_root, book_id):
        self.books_root = Path(books_root)
        self.book_id = book_id
        self.root = self.books_root / book_id / "illustration-proofs"
        self.events_path = self.root / "generation-ledger.jsonl"

    def events(self):
        if not self.events_path.exists():
            return []
        events = []
        with self.events_path.open("r", encoding="utf-8") as handle:
            for number, line in enumerate(handle, 1):
                if line.strip():
                    event = json.loads(line)
                    if event.get("sequence") != number:
                        raise ContractError("proof generation ledger sequence is not contiguous")
                    events.append(event)
        return events

    def _append(self, event):
        events = self.events()
        record = dict(event)
        record.update({
            "schema_version": "1.0",
            "sequence": len(events) + 1,
            "book_id": self.book_id,
            "timestamp": utc_now(),
        })
        record["event_id"] = stable_id("proof-event", self.book_id, record["sequence"], record["operation_key"], record["status"])
        append_jsonl(self.events_path, record)
        return record

    def prepare(self, request, spending_policy):
        if request["book_id"] != self.book_id:
            raise ContractError("proof request book identity mismatch")
        existing = [event for event in self.events() if event["operation_key"] == request["operation_key"]]
        if existing:
            request_path = self.root / "requests" / (request["request_hash"] + ".json")
            return {"event": existing[0], "request_path": str(request_path), "idempotent": True}
        intents = [event for event in self.events() if event["status"] == "INTENT_RECORDED"]
        proof_intents = [event for event in intents if event["proof_id"] == request["proof_id"]]
        if len(proof_intents) >= MAX_ATTEMPTS_PER_PROOF or len(intents) >= MAX_ATTEMPTS_TOTAL:
            raise ContractError("proof generation attempt ceiling reached")
        if request["attempt_number"] != len(proof_intents) + 1:
            raise ContractError("proof attempt number is not the next durable attempt")
        estimate = request["estimated_cost_minor_units"]
        if estimate > 0:
            if not spending_policy.get("paid_calls_enabled"):
                raise BudgetExceededError("paid image generation is not authorized")
            if estimate > spending_policy.get("job_max_minor_units", 0):
                raise BudgetExceededError("image estimate exceeds the explicit job cap")
        elif request.get("paid_operation"):
            raise ContractError("paid operation cannot claim zero estimated cost")
        request_path = self.root / "requests" / (request["request_hash"] + ".json")
        if request_path.exists() and load_json(request_path) != request:
            raise ContractError("proof request hash collision")
        if not request_path.exists():
            atomic_json_write(request_path, request)
        event = self._append({
            "status": "INTENT_RECORDED",
            "proof_id": request["proof_id"],
            "attempt_number": request["attempt_number"],
            "operation_key": request["operation_key"],
            "request_hash": request["request_hash"],
            "estimated_cost_minor_units": estimate,
            "paid_operation": request["paid_operation"],
        })
        return {"event": event, "request_path": str(request_path), "idempotent": False}

    def import_image(self, request, source_path, provider_receipt):
        events = self.events()
        intents = [event for event in events if event["operation_key"] == request["operation_key"] and event["status"] == "INTENT_RECORDED"]
        if len(intents) != 1:
            raise ContractError("proof image import requires one durable generation intent")
        successes = [event for event in events if event["operation_key"] == request["operation_key"] and event["status"] == "SUCCEEDED"]
        if successes:
            receipt_path = self.root / "receipts" / (successes[-1]["receipt_hash"] + ".json")
            return load_json(receipt_path), True
        if provider_receipt.get("provider_id") != request["provider_id"]:
            raise ContractError("provider receipt does not match the request")
        if provider_receipt.get("operation_key") != request["operation_key"]:
            raise ContractError("provider receipt does not bind the operation")
        actual_cost = provider_receipt.get("actual_cost_minor_units")
        if not isinstance(actual_cost, int) or actual_cost < 0:
            raise ContractError("provider receipt requires non-negative integer actual cost")
        if actual_cost > request["estimated_cost_minor_units"]:
            raise BudgetExceededError("actual image cost exceeds its reserved estimate")
        temporary_destination = self.root / "work" / (request["operation_key"] + ".png")
        framing = normalize_to_canvas(source_path, temporary_destination)
        output = framing["output"]
        existing_hashes = {
            event.get("image_hash") for event in events if event.get("status") == "SUCCEEDED"
        }
        if output["sha256"] in existing_hashes:
            temporary_destination.unlink()
            raise ContractError("duplicate proof image content is not accepted")
        filename = "attempt-%02d-%s.png" % (request["attempt_number"], output["sha256"][:16])
        final_path = self.root / "images" / request["proof_id"] / filename
        atomic_write(final_path, temporary_destination.read_bytes())
        temporary_destination.unlink()
        relative_path = final_path.relative_to(self.books_root.parent).as_posix()
        receipt = {
            "schema_version": "1.0",
            "book_id": self.book_id,
            "proof_id": request["proof_id"],
            "page_id": request["page_id"],
            "attempt_number": request["attempt_number"],
            "generation_version": request["attempt_number"],
            "operation_key": request["operation_key"],
            "request_hash": request["request_hash"],
            "proof_spec_hash": request["proof_spec_hash"],
            "character_reference_ids": request["character_reference_ids"],
            "source_hashes": {
                "manuscript": request["manuscript_hash"],
                "proof_package": request["proof_package_hash"],
                "rules": request["rules_hash"],
                "character_registry": request["character_registry_hash"],
            },
            "producer": provider_receipt["producer"],
            "provider": {
                "provider_id": provider_receipt["provider_id"],
                "model": provider_receipt.get("model", request["model"]),
                "provider_request_id": provider_receipt["provider_request_id"],
                "integration": request["integration"],
            },
            "image": dict(output, path=relative_path),
            "framing": framing,
            "estimated_cost_minor_units": request["estimated_cost_minor_units"],
            "actual_cost_minor_units": actual_cost,
            "currency": request["currency"],
            "status": "GENERATED_AWAITING_INDEPENDENT_VISUAL_REVIEW",
            "created_at": utc_now(),
        }
        receipt_hash = content_hash(receipt)
        receipt["receipt_hash"] = receipt_hash
        receipt["id"] = stable_id("proof-receipt", self.book_id, request["proof_id"], receipt_hash)
        receipt_path = self.root / "receipts" / (receipt_hash + ".json")
        atomic_json_write(receipt_path, receipt)
        self._append({
            "status": "SUCCEEDED",
            "proof_id": request["proof_id"],
            "attempt_number": request["attempt_number"],
            "operation_key": request["operation_key"],
            "request_hash": request["request_hash"],
            "receipt_hash": receipt_hash,
            "image_hash": output["sha256"],
            "image_path": relative_path,
            "actual_cost_minor_units": actual_cost,
        })
        return receipt, False

    def record_failure(self, request, provider_receipt):
        if provider_receipt.get("operation_key") != request["operation_key"]:
            raise ContractError("failure receipt does not bind the operation")
        prior = [event for event in self.events() if event["operation_key"] == request["operation_key"] and event["status"] == "FAILED"]
        if prior:
            return prior[-1]
        return self._append({
            "status": "FAILED",
            "proof_id": request["proof_id"],
            "attempt_number": request["attempt_number"],
            "operation_key": request["operation_key"],
            "request_hash": request["request_hash"],
            "provider_request_id": provider_receipt.get("provider_request_id"),
            "failure_code": provider_receipt.get("failure_code", "UNKNOWN_PROVIDER_FAILURE"),
            "failure_detail": provider_receipt.get("failure_detail", "No detail supplied"),
            "ambiguous_external_result": bool(provider_receipt.get("ambiguous_external_result")),
        })


def validate_proof_receipts(repository_root, receipts):
    repository_root = Path(repository_root)
    findings = []
    seen_hashes = set()
    attempts = {}
    for receipt in receipts:
        proof_id = receipt.get("proof_id")
        attempts[proof_id] = attempts.get(proof_id, 0) + 1
        image = receipt.get("image", {})
        path = repository_root / image.get("path", "")
        try:
            actual = inspect_png(path)
        except ContractError as exc:
            findings.append({"code": "IMAGE_INVALID", "proof_id": proof_id, "message": str(exc)})
            continue
        if actual["sha256"] != image.get("sha256"):
            findings.append({"code": "IMAGE_HASH_MISMATCH", "proof_id": proof_id})
        if (actual["width"], actual["height"]) != (1086, 1448):
            findings.append({"code": "IMAGE_DIMENSION_MISMATCH", "proof_id": proof_id})
        if actual["sha256"] in seen_hashes:
            findings.append({"code": "DUPLICATE_IMAGE", "proof_id": proof_id})
        seen_hashes.add(actual["sha256"])
        if not receipt.get("proof_spec_hash") or not receipt.get("request_hash"):
            findings.append({"code": "ARTIFACT_BINDING_INCOMPLETE", "proof_id": proof_id})
        if receipt.get("actual_cost_minor_units", 0) > receipt.get("estimated_cost_minor_units", 0):
            findings.append({"code": "SPENDING_LIMIT_EXCEEDED", "proof_id": proof_id})
    for proof_id, count in attempts.items():
        if count > MAX_ATTEMPTS_PER_PROOF:
            findings.append({"code": "PROOF_ATTEMPT_LIMIT_EXCEEDED", "proof_id": proof_id})
    if len(receipts) > MAX_ATTEMPTS_TOTAL:
        findings.append({"code": "TOTAL_ATTEMPT_LIMIT_EXCEEDED"})
    return {"result": "PASS" if not findings else "FIX", "findings": findings}


def finalize_visual_review(request, response, repository_root):
    if response.get("request_hash") != request.get("request_hash"):
        raise ContractError("visual review does not bind the request")
    if response.get("result") not in REVIEW_RESULTS:
        raise ContractError("visual review result must be PASS, FIX, or ESCALATE")
    if not response.get("actual_pixels_inspected"):
        raise ContractError("visual review must attest inspection of actual pixels")
    if response.get("reviewer", {}).get("id") == request.get("producer", {}).get("id"):
        raise ContractError("visual reviewer must be independent from the producing worker")
    if {item.get("dimension") for item in response.get("dimension_assessments", [])} != set(REVIEW_DIMENSIONS):
        raise ContractError("visual review dimension set is incomplete")
    image_path = Path(repository_root) / request["image"]["path"]
    image = inspect_png(image_path)
    if image["sha256"] != request["image"]["sha256"]:
        raise ContractError("visual review image hash is stale")
    if response["result"] == "PASS" and any(item.get("result") != "PASS" for item in response["dimension_assessments"]):
        raise ContractError("visual PASS cannot contain non-PASS dimensions")
    record = deepcopy(response)
    record.update({
        "schema_version": "1.0",
        "book_id": request["book_id"],
        "proof_id": request["proof_id"],
        "page_id": request["page_id"],
        "image": request["image"],
        "proof_spec_hash": request["proof_spec_hash"],
        "producer": request["producer"],
        "reviewed_at": utc_now(),
        "approval_claimed": False,
    })
    record["review_hash"] = content_hash(record)
    record["id"] = stable_id("visual-review", record["book_id"], record["proof_id"], record["review_hash"])
    return record


def visual_review_request(receipt):
    request = {
        "schema_version": "1.0",
        "book_id": receipt["book_id"],
        "proof_id": receipt["proof_id"],
        "page_id": receipt["page_id"],
        "image": receipt["image"],
        "proof_spec_hash": receipt["proof_spec_hash"],
        "request_hash_source": receipt["request_hash"],
        "producer": receipt["producer"],
        "required_dimensions": list(REVIEW_DIMENSIONS),
        "required_result": sorted(REVIEW_RESULTS),
        "actual_pixels_required": True,
        "independence_required": True,
    }
    request["request_hash"] = content_hash(request)
    return request


def build_contact_sheet_svg(repository_root, receipts, reviews, destination):
    repository_root = Path(repository_root)
    destination = Path(destination)
    review_by_hash = {item["image"]["sha256"]: item for item in reviews}
    cards = []
    for receipt in receipts:
        image_path = repository_root / receipt["image"]["path"]
        actual = inspect_png(image_path)
        if actual["sha256"] != receipt["image"]["sha256"]:
            raise ContractError("contact sheet image hash mismatch")
        review = review_by_hash.get(actual["sha256"])
        encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
        cards.append((receipt, review, encoded))
    if not cards:
        raise ContractError("contact sheet requires at least one real proof image")
    width = 2320
    card_width = 1086
    card_height = 1735
    rows = (len(cards) + 1) // 2
    height = 120 + rows * card_height + 80
    fragments = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">' % (width, height, width, height),
        '<rect width="100%%" height="100%%" fill="#071F35"/>',
        '<text x="80" y="70" fill="#F0CF76" font-family="Georgia,serif" font-size="38">DM04 — PR6 Illustration Proof Contact Sheet</text>',
    ]
    for index, (receipt, review, encoded) in enumerate(cards):
        column = index % 2
        row = index // 2
        x = 60 + column * 1140
        y = 110 + row * card_height
        fragments.extend([
            '<rect x="%d" y="%d" width="1086" height="1680" rx="10" fill="#FFF9EF" stroke="#D8AC4E" stroke-width="8"/>' % (x, y),
            '<image x="%d" y="%d" width="966" height="1288" preserveAspectRatio="xMidYMid meet" href="data:image/png;base64,%s"/>' % (x + 60, y + 55, encoded),
        ])
        metadata = [
            "Proof: %s" % receipt["proof_id"],
            "Page: %s" % receipt["page_id"],
            "Generation: v%d" % receipt["generation_version"],
            "Spec: %s" % receipt["proof_spec_hash"][:20],
            "Image: %s" % receipt["image"]["sha256"][:20],
            "Visual QA: %s" % (review["result"] if review else "PENDING"),
        ]
        for line_number, line in enumerate(metadata):
            fragments.append(
                '<text x="%d" y="%d" fill="#251C18" font-family="Georgia,serif" font-size="24">%s</text>'
                % (x + 60, y + 1390 + line_number * 42, html.escape(line))
            )
    fragments.append("</svg>")
    atomic_write(destination, ("\n".join(fragments) + "\n").encode("utf-8"))
    metadata = {
        "schema_version": "1.0",
        "book_id": receipts[0]["book_id"],
        "contact_sheet_path": destination.relative_to(repository_root).as_posix(),
        "contact_sheet_hash": sha256_bytes(destination.read_bytes()),
        "format": "SVG_WITH_EMBEDDED_REAL_PNG_PIXELS",
        "proofs": [
            {
                "proof_id": receipt["proof_id"],
                "page_id": receipt["page_id"],
                "generation_version": receipt["generation_version"],
                "proof_spec_hash": receipt["proof_spec_hash"],
                "image_hash": receipt["image"]["sha256"],
                "visual_qa_status": review_by_hash.get(receipt["image"]["sha256"], {}).get("result", "PENDING"),
            } for receipt in receipts
        ],
    }
    metadata["metadata_hash"] = content_hash(metadata)
    metadata_path = destination.with_suffix(".json")
    atomic_json_write(metadata_path, metadata)
    return metadata


def build_style_approval_request(book_id, receipts, reviews, character_registry_hash,
                                 proof_package_hash, source_hashes, contact_sheet):
    review_by_image = {item["image"]["sha256"]: item for item in reviews}
    assets = []
    for receipt in receipts:
        review = review_by_image.get(receipt["image"]["sha256"])
        assets.append({
            "proof_id": receipt["proof_id"],
            "page_id": receipt["page_id"],
            "proof_spec_hash": receipt["proof_spec_hash"],
            "image_hash": receipt["image"]["sha256"],
            "image_path": receipt["image"]["path"],
            "character_reference_ids": receipt.get("character_reference_ids", []),
            "visual_review_hash": review.get("review_hash") if review else None,
            "visual_review_result": review.get("result") if review else "PENDING",
        })
    request = {
        "schema_version": "1.0",
        "book_id": book_id,
        "approval_type": "VISUAL_STYLE_OR_CHARACTER_FAMILY",
        "status": "AWAITING_STYLE_APPROVAL",
        "decision": None,
        "human_approver_required": True,
        "self_approval_prohibited": True,
        "proof_package_hash": proof_package_hash,
        "character_registry_hash": character_registry_hash,
        "source_hashes": source_hashes,
        "contact_sheet": contact_sheet,
        "assets": assets,
        "inheritance_policy": "Style parameters may be inherited only with exact approved hashes; character and theological approvals never transfer to unrelated subjects.",
    }
    request["approval_request_hash"] = content_hash(request)
    request["id"] = stable_id("style-approval-request", book_id, request["approval_request_hash"])
    return request


def store_snapshot(store_class, books_root, book_id, payload):
    store = store_class(books_root)
    versions = store.versions(book_id)
    if versions and versions[-1]["payload"] == payload:
        return versions[-1]
    return store.put(book_id, payload, versions[-1]["content_hash"] if versions else None)
