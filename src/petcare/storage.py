"""Local-first JSON storage for pet care records.

All data lives in a single JSON file under the user's home directory by
default. Nothing is ever sent off the machine.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable

from .models import Entry


DEFAULT_DIR = Path.home() / ".petcare"
DEFAULT_FILE = DEFAULT_DIR / "records.json"


class Storage:
    """Append-safe, crash-tolerant JSON record store."""

    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path else DEFAULT_FILE
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._entries: list[Entry] = []
        self._load()

    # ---- internal ------------------------------------------------------------

    def _load(self) -> None:
        if not self.path.exists():
            self._entries = []
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            self._entries = []
            return
        if not isinstance(raw, list):
            self._entries = []
            return
        self._entries = [Entry.from_dict(item) for item in raw if isinstance(item, dict)]

    def _next_id(self) -> int:
        existing = [e.id for e in self._entries if e.id is not None]
        return (max(existing) + 1) if existing else 1

    def _write(self) -> None:
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        data = json.dumps([e.to_dict() for e in self._entries], indent=2, ensure_ascii=False)
        tmp.write_text(data, encoding="utf-8")
        tmp.replace(self.path)  # atomic on POSIX

    # ---- public --------------------------------------------------------------

    def add(self, entry: Entry) -> Entry:
        entry.id = self._next_id()
        self._entries.append(entry)
        self._write()
        return entry

    def all(self) -> list[Entry]:
        return list(self._entries)

    def filter(self, **filters) -> list[Entry]:
        result = []
        for e in self._entries:
            if all(getattr(e, k, None) == v for k, v in filters.items()):
                result.append(e)
        return result

    def clear(self) -> None:
        self._entries = []
        self._write()

    def count(self) -> int:
        return len(self._entries)

    def iter_entries(self) -> Iterable[Entry]:
        return iter(self._entries)