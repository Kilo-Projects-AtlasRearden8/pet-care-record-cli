"""CSV export and printable care-sheet rendering."""

from __future__ import annotations

import csv
from datetime import date
from io import StringIO
from pathlib import Path
from typing import Iterable

from .models import Entry, today


CSV_COLUMNS = ["id", "kind", "pet", "name", "date", "details", "next_due"]


def render_csv(entries: Iterable[Entry]) -> str:
    """Render entries as CSV text with a header row."""
    buf = StringIO()
    writer = csv.DictWriter(buf, fieldnames=CSV_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for e in sorted(entries, key=lambda x: (x.date, x.id or 0)):
        writer.writerow(e.to_dict())
    return buf.getvalue()


def write_csv(entries: Iterable[Entry], path: Path | str) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_csv(entries), encoding="utf-8")
    return out


# --------------------------------------------------------------------------- #
# Printable care sheet
# --------------------------------------------------------------------------- #


def _bar(text: str, width: int = 60) -> str:
    return "+" + "-" * (width - 2) + "+\n" + f"| {text}".ljust(width - 1) + "|\n" + "+" + "-" * (width - 2) + "+"


def _row(left: str, right: str, width: int = 60) -> str:
    gap = width - len(left) - len(right) - 3
    if gap < 1:
        gap = 1
    return f"| {left}{' ' * gap}{right} " + " " * (width - len(left) - gap - len(right) - 3) + "|\n"


def render_care_sheet(entries: Iterable[Entry], *, pet: str | None = None, generated: date | None = None) -> str:
    """Render a plain-text, printable care sheet for a sitter."""
    gen = generated or today()
    items = sorted(entries, key=lambda x: (x.date, x.id or 0))
    if pet:
        items = [e for e in items if e.pet.lower() == pet.lower()]

    width = 60
    lines: list[str] = []
    lines.append("+" + "=" * (width - 2) + "+")
    lines.append("|" + " PET CARE SHEET".center(width - 2) + "|")
    lines.append("+" + "=" * (width - 2) + "+")
    lines.append(_row("Generated:", gen.isoformat(), width).rstrip("\n"))
    if pet:
        lines.append(_row("Pet:", pet, width).rstrip("\n"))
    lines.append("+" + "-" * (width - 2) + "+")

    grouped: dict[str, list[Entry]] = {}
    for e in items:
        grouped.setdefault(e.kind, []).append(e)

    if not items:
        lines.append("|" + "(no records)".center(width - 2) + "|")
    else:
        for kind in ("medication", "vet_visit", "vaccination", "note"):
            group = grouped.get(kind, [])
            if not group:
                continue
            label = kind.replace("_", " ").upper()
            lines.append("|" + f" {label}".ljust(width - 1) + "|")
            lines.append("+" + "-" * (width - 2) + "+")
            for e in group:
                lines.append(_row("  Name:", e.name, width).rstrip("\n"))
                lines.append(_row("  Date:", e.date, width).rstrip("\n"))
                if e.details:
                    lines.append(_row("  Notes:", e.details, width).rstrip("\n"))
                if e.next_due:
                    lines.append(_row("  Next due:", e.next_due, width).rstrip("\n"))
                lines.append("+" + "-" * (width - 2) + "+")

    lines.append("+" + "=" * (width - 2) + "+")
    lines.append("Local-first storage: ~/.petcare/records.json (never shared).")
    return "\n".join(lines) + "\n"


def write_care_sheet(entries: Iterable[Entry], path: Path | str, **kwargs) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_care_sheet(entries, **kwargs), encoding="utf-8")
    return out