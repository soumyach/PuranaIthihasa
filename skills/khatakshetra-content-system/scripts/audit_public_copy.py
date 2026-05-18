#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
PATTERN = re.compile(
    r"\b(seed story|seed experience|placeholder|todo|content graph|kg|linked nodes|story nodes|"
    r"signup validation|badge theater|prototype|production version|needs exact source validation|"
    r"source validation required|planned|launch-candidate)\b",
    re.IGNORECASE,
)

paths = []
for suffix in ("*.html", "content/*.json", "content/story-packs/*.json"):
    paths.extend(ROOT.glob(suffix))

def should_skip_line(line: str) -> bool:
    technical = (
        "::placeholder",
        "placeholder=",
        ".placeholder",
        "pack.kg",
        '"kg"',
        '"kg":',
        '"inputs":',
        "content/experience-engine",
    )
    return any(token in line for token in technical)

hits = []
for path in sorted(paths):
    if path.name == "experience-engine.json":
        continue
    text = path.read_text(encoding="utf-8")
    for idx, line in enumerate(text.splitlines(), 1):
        if should_skip_line(line):
            continue
        if PATTERN.search(line):
            hits.append(f"{path.relative_to(ROOT)}:{idx}: {line.strip()[:180]}")

if hits:
    print("\n".join(hits))
    sys.exit(1)

print("public copy audit ok")
