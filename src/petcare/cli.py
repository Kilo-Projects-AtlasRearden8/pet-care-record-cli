"""Command-line interface for petcare."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from . import __version__
from .export import render_csv, render_care_sheet, write_csv, write_care_sheet
from .models import Entry, VALID_KINDS, parse_date, today, days_until, is_due
from .storage import Storage


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="petcare",
        description="Log pet medications, vet visits, vaccinations, and care notes. Local-first, no keys.",
    )
    parser.add_argument("--data", default=None, help="Path to JSON storage file (default: ~/.petcare/records.json)")
    parser.add_argument("--version", action="version", version=f"petcare {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="Add a care entry")
    add.add_argument("kind", choices=VALID_KINDS)
    add.add_argument("pet")
    add.add_argument("name")
    add.add_argument("date", help="YYYY-MM-DD")
    add.add_argument("--details", default="")
    add.add_argument("--next-due", dest="next_due", default=None, help="YYYY-MM-DD")

    sub.add_parser("list", help="List all entries")

    export = sub.add_parser("export", help="Export entries to CSV")
    export.add_argument("path")
    export.add_argument("--pet", default=None)

    sheet = sub.add_parser("sheet", help="Write a printable care sheet")
    sheet.add_argument("path")
    sheet.add_argument("--pet", default=None)

    sub.add_parser("due", help="Show entries with upcoming due dates")

    return parser


def _store(args) -> Storage:
    return Storage(getattr(args, "data", None))


def cmd_add(args) -> int:
    entry = Entry.create(
        kind=args.kind,
        pet=args.pet,
        name=args.name,
        date_value=args.date,
        details=args.details,
        next_due=args.next_due,
    )
    store = _store(args)
    entry = store.add(entry)
    print(f"Added {entry.kind} entry #{entry.id} for {entry.pet} ({entry.name}) on {entry.date}.")
    return 0


def cmd_list(args) -> int:
    store = _store(args)
    entries = sorted(store.all(), key=lambda e: (e.date, e.id or 0))
    if not entries:
        print("No entries yet. Try: petcare add medication <pet> <name> <date>")
        return 0
    for e in entries:
        due = ""
        if e.next_due:
            days = days_until(parse_date(e.next_due))
            marker = "DUE" if is_due(parse_date(e.next_due)) else f"in {days}d"
            due = f"  next due {e.next_due} ({marker})"
        print(f"[{e.id}] {e.kind:<12} {e.pet:<10} {e.name:<20} {e.date}{due}")
    return 0


def cmd_export(args) -> int:
    store = _store(args)
    entries = store.filter(pet=args.pet) if args.pet else store.all()
    path = write_csv(entries, args.path)
    print(f"Wrote {len(entries)} rows to {path}")
    return 0


def cmd_sheet(args) -> int:
    store = _store(args)
    entries = store.filter(pet=args.pet) if args.pet else store.all()
    path = write_care_sheet(entries, args.path, pet=args.pet)
    print(f"Wrote care sheet to {path}")
    return 0


def cmd_due(args) -> int:
    store = _store(args)
    today_ = today()
    upcoming = [e for e in store.all() if e.next_due and not is_due(parse_date(e.next_due))]
    if not upcoming:
        print("No upcoming due dates.")
        return 0
    for e in sorted(upcoming, key=lambda x: x.next_due or ""):
        days = days_until(parse_date(e.next_due), now=today_)
        print(f"[{e.id}] {e.kind:<12} {e.pet:<10} {e.name:<20} due {e.next_due} ({days}d)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    handlers = {
        "add": cmd_add,
        "list": cmd_list,
        "export": cmd_export,
        "sheet": cmd_sheet,
        "due": cmd_due,
    }
    handler = handlers.get(args.command)
    if handler is None:  # pragma: no cover - argparse enforces subcommand
        parser.print_help()
        return 1
    try:
        return handler(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())