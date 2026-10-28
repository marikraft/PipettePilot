"""
Append-only audit trail for each session, one JSON record per line.

Every record names who did what and when, and carries the hash of the record before it,
so a line edited or removed after the fact breaks the chain (see verify()). This makes the
log tamper-evident, not tamper-proof: it is a prototype, not a validated 21 CFR Part 11 system.
"""
import getpass
import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

GENESIS = "0" * 64


def _hash(record: dict) -> str:
    return hashlib.sha256(json.dumps(record, sort_keys=True).encode("utf-8")).hexdigest()


class AuditLog:
    def __init__(self, directory: str = "logs"):
        self.session_id = uuid.uuid4().hex[:12]
        self.user = getpass.getuser()
        Path(directory).mkdir(exist_ok=True)
        self.path = Path(directory) / f"audit_{self.session_id}.jsonl"
        self._last_hash = GENESIS

    def record(self, event: str, **data) -> None:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "session_id": self.session_id,
            "user": self.user,
            "event": event,
            "data": data,
            "prev_hash": self._last_hash,
        }
        entry["hash"] = _hash(entry)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        self._last_hash = entry["hash"]


def verify(path) -> tuple[bool, str]:
    """Recompute the hash chain. Returns (ok, message)."""
    previous = GENESIS
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            entry = json.loads(line)
            stored = entry.pop("hash")
            if entry["prev_hash"] != previous:
                return False, f"Line {n}: chain broken (a record before it was changed or removed)."
            if _hash(entry) != stored:
                return False, f"Line {n}: contents don't match the stored hash."
            previous = stored
    return True, "Audit trail intact."
