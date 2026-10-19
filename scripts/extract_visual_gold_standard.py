#!/usr/bin/env python3
"""Extract or verify the eight PR7 Visual Gold Standard pages.

The registered PDFs remain ignored local references.  This script verifies their
exact identities before invoking Poppler and refuses to replace a curated page
when the newly rendered pixels do not match the manifest hash.
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "book-factory" / "references" / "visual-gold-standard" / "manifest.json"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_manifest():
    with MANIFEST.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def verify_file(path, expected_hash, expected_bytes=None):
    if not path.is_file():
        raise SystemExit("missing required file: %s" % path)
    actual = sha256(path)
    if actual != expected_hash:
        raise SystemExit("hash mismatch for %s: %s" % (path, actual))
    if expected_bytes is not None and path.stat().st_size != expected_bytes:
        raise SystemExit("byte-size mismatch for %s" % path)


def verify(manifest, require_sources=True):
    assets = {item["asset_id"]: item for item in manifest["source_assets"]}
    if require_sources:
        for asset in assets.values():
            verify_file(ROOT / asset["path"], asset["sha256"], asset["bytes"])
    for page in manifest["pages"]:
        if page["source_asset_id"] not in assets:
            raise SystemExit("unknown source asset for %s" % page["reference_id"])
        verify_file(ROOT / page["extracted_path"], page["extracted_sha256"], page["bytes"])


def extract(manifest):
    executable = shutil.which("pdftoppm")
    if not executable:
        raise SystemExit("pdftoppm is required for extraction")
    assets = {item["asset_id"]: item for item in manifest["source_assets"]}
    for asset in assets.values():
        verify_file(ROOT / asset["path"], asset["sha256"], asset["bytes"])
    with tempfile.TemporaryDirectory(prefix="khatakshetra-gold-standard-") as temporary:
        temporary_root = Path(temporary)
        for page in manifest["pages"]:
            asset = assets[page["source_asset_id"]]
            output_stem = temporary_root / page["reference_id"]
            command = [
                executable,
                "-f", str(page["original_pdf_page"]),
                "-l", str(page["original_pdf_page"]),
                "-singlefile",
                "-png",
                "-r", str(manifest["extraction"]["dpi"]),
                str(ROOT / asset["path"]),
                str(output_stem),
            ]
            completed = subprocess.run(command, capture_output=True, text=True, check=False)
            if completed.returncode:
                raise SystemExit("page extraction failed for %s: %s" % (
                    page["reference_id"], completed.stderr.strip()
                ))
            rendered = output_stem.with_suffix(".png")
            verify_file(rendered, page["extracted_sha256"], page["bytes"])
            destination = ROOT / page["extracted_path"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                verify_file(destination, page["extracted_sha256"], page["bytes"])
            else:
                shutil.copyfile(rendered, destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extract", action="store_true", help="render the selected pages after verifying both source PDFs")
    parser.add_argument("--allow-missing-sources", action="store_true", help="verify only tracked page assets when ignored local PDFs are unavailable")
    args = parser.parse_args()
    manifest = load_manifest()
    if args.extract:
        extract(manifest)
    verify(manifest, require_sources=not args.allow_missing_sources)
    print(json.dumps({
        "status": "PASS",
        "manifest": str(MANIFEST.relative_to(ROOT)),
        "pages": len(manifest["pages"]),
        "source_pdfs_verified": not args.allow_missing_sources,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
