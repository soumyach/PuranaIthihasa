"""Single-active-book lease implemented without external dependencies."""

import json
import os
from pathlib import Path

from .errors import LeaseError
from .util import utc_now


class BookLease:
    def __init__(self, runtime_root):
        self.path = Path(runtime_root) / "active-book.lease"

    def acquire(self, book_id, owner):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"book_id": book_id, "owner": owner, "acquired_at": utc_now()}
        try:
            descriptor = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        except FileExistsError:
            with self.path.open("r", encoding="utf-8") as handle:
                active = json.load(handle)
            if active.get("book_id") == book_id and active.get("owner") == owner:
                return active
            raise LeaseError("book %s is already active under owner %s" % (active.get("book_id"), active.get("owner")))
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
        return payload

    def release(self, book_id, owner):
        if not self.path.exists():
            return
        with self.path.open("r", encoding="utf-8") as handle:
            active = json.load(handle)
        if active.get("book_id") != book_id or active.get("owner") != owner:
            raise LeaseError("only the lease owner may release it")
        self.path.unlink()
