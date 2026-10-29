"""Data models and date math for pet care records."""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from datetime import date, datetime, timedelta
from typing import Any


_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parse_date(value: str) -> date:
    """Parse an ISO-8601 YYYY-MM-DD date string into a :class:`date`.

    Raises :class:`ValueError` on invalid input.
    """
    if not isinstance(value, str) or not _DATE_RE.match(value.strip()):
        raise ValueError(f"Invalid date {value!r}; expected YYYY-MM-DD")
    try:
        return date.fromisoformat(value.strip())
    except ValueError as exc:  # pragma: no cover - covered by regex guard
        raise ValueError(f"Invalid date {value!r}; expected YYYY-MM-DD") from exc


def today() -> date:
    """Return today's date (centralised for testability)."""
    return date.today()


def add_days(d: date, days: int) -> date:
    """Return ``d`` plus ``days`` calendar days."""
    return d + timedelta(days=days)


def days_between(a: date, b: date) -> int:
    """Whole days from ``a`` to ``b`` (positive when ``b`` is later)."""
    return (b - a).days


def days_until(d: date, *, now: date | None = None) -> int:
    """Days remaining until ``d`` relative to ``now`` (defaults to today)."""
    ref = now if now is not None else today()
    return (d - ref).days


def is_due(d: date, *, now: date | None = None, window: int = 0) -> bool:
    """Return True if ``d`` falls on or before ``now + window`` days."""
    ref = now if now is not None else today()
    return d <= ref + timedelta(days=window)


@dataclass
class Entry:
    """A single care record of any kind."""

    kind: str  # medication | vet_visit | vaccination | note
    pet: str
    name: str
    date: str  # stored as YYYY-MM-DD
    details: str = ""
    next_due: str | None = None
    id: int | None = None

    # ---- construction helpers -------------------------------------------------

    @classmethod
    def create(
        cls,
        kind: str,
        pet: str,
        name: str,
        date_value: str,
        details: str = "",
        next_due: str | None = None,
    ) -> "Entry":
        parse_date(date_value)
        if next_due:
            parse_date(next_due)
        return cls(
            kind=validate_kind(kind),
            pet=pet,
            name=name,
            date=date_value,
            details=details,
            next_due=next_due,
        )

    # ---- date math -----------------------------------------------------------

    def date_obj(self) -> date:
        return parse_date(self.date)

    def next_due_obj(self) -> date | None:
        return parse_date(self.next_due) if self.next_due else None

    def days_until_due(self, *, now: date | None = None) -> int | None:
        nd = self.next_due_obj()
        if nd is None:
            return None
        return days_until(nd, now=now)

    def is_due(self, *, now: date | None = None, window: int = 0) -> bool:
        nd = self.next_due_obj()
        if nd is None:
            return False
        return is_due(nd, now=now, window=window)

    # ---- serialisation -------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Entry":
        return cls(
            kind=data["kind"],
            pet=data["pet"],
            name=data["name"],
            date=data["date"],
            details=data.get("details", ""),
            next_due=data.get("next_due"),
            id=data.get("id"),
        )

    def display_date(self) -> str:
        return self.date

    def summary(self) -> str:
        bits = [f"{self.kind}", f"pet={self.pet}", f"name={self.name}", f"date={self.date}"]
        if self.details:
            bits.append(f"details={self.details}")
        if self.next_due:
            bits.append(f"next_due={self.next_due}")
        return " ".join(bits)


VALID_KINDS = ("medication", "vet_visit", "vaccination", "note")


def validate_kind(kind: str) -> str:
    k = kind.strip().lower()
    if k not in VALID_KINDS:
        raise ValueError(f"Unknown kind {kind!r}; expected one of {VALID_KINDS}")
    return k