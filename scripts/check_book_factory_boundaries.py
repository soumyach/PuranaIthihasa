#!/usr/bin/env python3
"""Offline CI checks for PR2 scope, hashes, and binary-storage boundaries."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAX_NORMAL_GIT_BYTES = 10 * 1024 * 1024
BINARY_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp"}


def main():
    errors = []
    warnings = []
    catalogue = (ROOT / "books" / "catalogue.json").read_text(encoding="utf-8")
    if "synthetic-foundation-book" in catalogue:
        errors.append("synthetic fixture leaked into the authoritative catalogue")
    registry = json.loads((ROOT / "book-factory" / "references" / "reference-assets.json").read_text(encoding="utf-8"))
    tracked = set(
        subprocess.run(
            ["git", "ls-files"],
            cwd=str(ROOT),
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
    )
    for item in registry["assets"]:
        relative = item["path"]
        expected = item["sha256"]
        if item.get("storage_mode") == "LOCAL_UNTRACKED_REFERENCE" and relative in tracked:
            errors.append("local-only reference asset is tracked by Git: %s" % relative)
        path = ROOT / relative
        if not path.is_file():
            warnings.append("optional local reference asset is unavailable: %s" % relative)
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            errors.append("registered reference asset hash mismatch: %s" % relative)
        if path.stat().st_size != item["bytes"]:
            errors.append("registered reference asset size mismatch: %s" % relative)
        if path.stat().st_size > 100 * 1024 * 1024:
            warnings.append("registered reference exceeds normal GitHub object size; storage policy required: %s" % relative)
    for path in (ROOT / "books").rglob("*"):
        if path.is_file() and path.suffix.lower() in BINARY_SUFFIXES and path.stat().st_size > MAX_NORMAL_GIT_BYTES:
            first_line = path.open("rb").readline()
            if first_line != b"version https://git-lfs.github.com/spec/v1\n":
                errors.append("large book binary is not an LFS pointer: %s" % path.relative_to(ROOT))
    diff = subprocess.run(
        ["git", "diff", "--exit-code", "--", "research/source-graph"],
        cwd=str(ROOT),
        check=False,
        capture_output=True,
        text=True,
    )
    if diff.returncode:
        errors.append("research/source-graph has working-tree changes")
    sys.path.insert(0, str(ROOT))
    from book_factory.util import tree_hash

    baseline = json.loads((ROOT / "book-factory" / "config" / "source-graph-baseline.json").read_text(encoding="utf-8"))
    actual_graph_hash = tree_hash(ROOT / "research" / "source-graph")
    if actual_graph_hash != baseline["graph_tree_sha256"]:
        errors.append("research/source-graph differs from the audited Foundation baseline")
    if errors:
        for error in errors:
            print("ERROR:", error)
        return 1
    for warning in warnings:
        print("WARNING:", warning)
    print("Book Factory boundary checks passed; source graph is clean and available reference assets match the registry.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
