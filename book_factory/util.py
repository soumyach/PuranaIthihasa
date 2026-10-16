"""Deterministic serialization, hashing, identifiers, and atomic writes."""

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_bytes(payload):
    return hashlib.sha256(payload).hexdigest()


def content_hash(value):
    if isinstance(value, bytes):
        payload = value
    elif isinstance(value, str):
        payload = value.encode("utf-8")
    else:
        payload = canonical_json(value).encode("utf-8")
    return sha256_bytes(payload)


def stable_id(kind, *parts):
    digest = content_hash({"kind": kind, "parts": [str(part) for part in parts]})[:24]
    return "%s-%s" % (kind, digest)


def load_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def atomic_write(path, payload):
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".%s." % destination.name, dir=str(destination.parent))
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
        directory_fd = os.open(str(destination.parent), os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def atomic_json_write(path, value):
    atomic_write(path, (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8"))


def append_jsonl(path, value):
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    line = (canonical_json(value) + "\n").encode("utf-8")
    descriptor = os.open(str(destination), os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o644)
    with os.fdopen(descriptor, "ab") as handle:
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())


def tree_snapshot(root):
    root = Path(root)
    files = {}
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
            continue
        files[path.relative_to(root).as_posix()] = sha256_bytes(path.read_bytes())
    return files


def tree_hash(root):
    return content_hash(tree_snapshot(root))
