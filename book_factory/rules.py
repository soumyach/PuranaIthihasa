from pathlib import Path

from .errors import BlockedError
from .util import sha256_bytes


RULES_FILENAME = "MYTHOLOGY_COMIC_RULES.md"


def rules_status(repository_root):
    path = Path(repository_root) / RULES_FILENAME
    if not path.is_file():
        return {
            "status": "BLOCKED_STANDARD",
            "path": str(path),
            "message": "%s is required; no fallback rules are permitted" % RULES_FILENAME,
        }
    return {
        "status": "AVAILABLE",
        "path": str(path),
        "sha256": sha256_bytes(path.read_bytes()),
    }


def require_rules(repository_root):
    status = rules_status(repository_root)
    if status["status"] != "AVAILABLE":
        raise BlockedError(status["message"], status)
    return status
