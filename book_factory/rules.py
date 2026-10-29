from pathlib import Path

from .errors import BlockedError
from .util import load_json, sha256_bytes


RULES_FILENAME = "MYTHOLOGY_COMIC_RULES.md"
REGISTRY_PATH = Path("book-factory/config/standards.json")


def rules_status(repository_root):
    root = Path(repository_root)
    path = root / RULES_FILENAME
    if not path.is_file():
        return {
            "status": "BLOCKED_STANDARD",
            "path": str(path),
            "message": "%s is required; no fallback rules are permitted" % RULES_FILENAME,
        }
    digest = sha256_bytes(path.read_bytes())
    registry_path = root / REGISTRY_PATH
    if not registry_path.is_file():
        return {
            "status": "BLOCKED_STANDARD_REGISTRY",
            "path": str(path),
            "sha256": digest,
            "message": "the authoritative rules registry is missing",
        }
    registry = load_json(registry_path)
    expected = registry.get("mythology_comic_rules", {}).get("sha256")
    if digest != expected:
        return {
            "status": "BLOCKED_STANDARD_HASH_MISMATCH",
            "path": str(path),
            "sha256": digest,
            "expected_sha256": expected,
            "message": "the rules file does not match the registered authoritative hash",
        }
    return {
        "status": "AVAILABLE",
        "path": str(path),
        "sha256": digest,
        "version": registry["mythology_comic_rules"]["version"],
    }


def require_rules(repository_root):
    status = rules_status(repository_root)
    if status["status"] != "AVAILABLE":
        raise BlockedError(status["message"], status)
    return status
