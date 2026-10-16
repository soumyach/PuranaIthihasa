#!/usr/bin/env python3
"""Offline CI checks for PR3 scope, hashes, and binary-storage boundaries."""

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
    immutable_inputs = {
        "book-factory/inputs/catalogues/Khatakshetra_Illustrated_Library_Catalogue_v0.1.json": "e80483a0c77e8453616868b85ce883407e7c5bfaa81fae5d6c605266764c2f5b",
        "book-factory/references/literary-benchmarks/The_Enemy_Who_Multiplied_Manuscript_v2.md": "6684d61e7c8f58a3fc3d851d7e8cbc7d13eb1e42105dbb9d011c1e7453791865",
    }
    for relative, expected in immutable_inputs.items():
        path = ROOT / relative
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            errors.append("immutable PR3 input is missing or changed: %s" % relative)
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
            warnings.append("registered reference exceeds normal GitHub object size and is correctly governed as local-only: %s" % relative)
    for path in (ROOT / "books").rglob("*"):
        if path.is_file() and path.suffix.lower() in BINARY_SUFFIXES and path.stat().st_size > MAX_NORMAL_GIT_BYTES:
            first_line = path.open("rb").readline()
            if first_line != b"version https://git-lfs.github.com/spec/v1\n":
                errors.append("large book binary is not an LFS pointer: %s" % path.relative_to(ROOT))
    reachable = subprocess.run(
        ["git", "rev-list", "--objects", "HEAD"], cwd=str(ROOT), check=True, capture_output=True, text=True
    ).stdout.splitlines()
    if reachable:
        object_ids = "\n".join(line.split(" ", 1)[0] for line in reachable) + "\n"
        inspected = subprocess.run(
            ["git", "cat-file", "--batch-check=%(objecttype) %(objectsize)"],
            cwd=str(ROOT), input=object_ids, check=True, capture_output=True, text=True,
        ).stdout.splitlines()
        if any(kind == "blob" and int(size) > 100 * 1024 * 1024 for kind, size in (line.split() for line in inspected)):
            errors.append("current Git history contains a blob above 100 MiB")
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
