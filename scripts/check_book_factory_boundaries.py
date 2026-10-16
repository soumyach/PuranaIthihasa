#!/usr/bin/env python3
"""Offline CI checks for PR1 scope and future binary-storage boundaries."""

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAX_NORMAL_GIT_BYTES = 10 * 1024 * 1024
BINARY_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp"}


def main():
    errors = []
    catalogue = (ROOT / "books" / "catalogue.json").read_text(encoding="utf-8")
    if "synthetic-foundation-book" in catalogue:
        errors.append("synthetic fixture leaked into the authoritative catalogue")
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
    print("Book Factory boundary checks passed; source graph is clean and no oversized book binaries were added.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
