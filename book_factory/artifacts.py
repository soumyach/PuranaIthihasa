"""Immutable content-addressed artifact storage."""

from pathlib import Path

from .errors import ContractError
from .util import atomic_json_write, atomic_write, sha256_bytes, stable_id, utc_now


class ArtifactStore:
    def __init__(self, books_root):
        self.root = Path(books_root) / "_artifacts" / "sha256"

    def put(self, payload, media_type="application/octet-stream", extension="bin", logical_id=None,
            input_hashes=None, version=1):
        if not isinstance(payload, bytes):
            raise ContractError("artifact payload must be bytes")
        digest = sha256_bytes(payload)
        safe_extension = extension.lower().lstrip(".")
        if not safe_extension.isalnum():
            raise ContractError("artifact extension must be alphanumeric")
        if not isinstance(version, int) or version < 1:
            raise ContractError("artifact version must be a positive integer")
        directory = self.root / digest[:2]
        artifact_path = directory / (digest + "." + safe_extension)
        metadata_path = directory / (digest + ".artifact.json")
        if artifact_path.exists() and artifact_path.read_bytes() != payload:
            raise ContractError("content hash collision")
        if not artifact_path.exists():
            atomic_write(artifact_path, payload)
        metadata = {
            "schema_version": "1.0",
            "id": stable_id("artifact", digest),
            "sha256": digest,
            "media_type": media_type,
            "extension": safe_extension,
            "logical_id": logical_id,
            "version": version,
            "input_hashes": sorted(input_hashes or []),
            "created_at": utc_now(),
            "path": artifact_path.relative_to(self.root.parents[1]).as_posix(),
        }
        if not metadata_path.exists():
            atomic_json_write(metadata_path, metadata)
        else:
            from .util import load_json

            metadata = load_json(metadata_path)
        return metadata
