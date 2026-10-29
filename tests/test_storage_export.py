"""Tests for storage and export logic."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pytest

from petcare.export import render_csv, render_care_sheet
from petcare.models import Entry, today
from petcare.storage import Storage


# --------------------------------------------------------------------------- #
# Storage
# --------------------------------------------------------------------------- #


def test_storage_add_and_load(tmp_path: Path):
    store = Storage(tmp_path / "r.json")
    e = Entry.create(kind="medication", pet="Rex", name="Flea", date_value="2026-10-01")
    store.add(e)
    store2 = Storage(tmp_path / "r.json")
    entries = store2.all()
    assert len(entries) == 1
    assert entries[0].id == 1
    assert entries[0].name == "Flea"


def test_storage_ids_increment(tmp_path: Path):
    store = Storage(tmp_path / "r.json")
    a = store.add(Entry.create(kind="note", pet="Rex", name="A", date_value="2026-10-01"))
    b = store.add(Entry.create(kind="note", pet="Rex", name="B", date_value="2026-10-02"))
    assert a.id == 1 and b.id == 2


def test_storage_filter(tmp_path: Path):
    store = Storage(tmp_path / "r.json")
    store.add(Entry.create(kind="medication", pet="Rex", name="A", date_value="2026-10-01"))
    store.add(Entry.create(kind="medication", pet="Milo", name="B", date_value="2026-10-02"))
    assert len(store.filter(pet="Rex")) == 1
    assert len(store.filter(kind="medication")) == 2


def test_storage_missing_file_is_empty(tmp_path: Path):
    store = Storage(tmp_path / "missing.json")
    assert store.all() == []
    assert store.count() == 0


def test_storage_corrupt_file_is_empty(tmp_path: Path):
    p = tmp_path / "bad.json"
    p.write_text("not json {", encoding="utf-8")
    store = Storage(p)
    assert store.all() == []


def test_storage_write_is_atomic(tmp_path: Path):
    p = tmp_path / "r.json"
    store = Storage(p)
    store.add(Entry.create(kind="note", pet="Rex", name="A", date_value="2026-10-01"))
    assert not (tmp_path / "r.json.tmp").exists()


# --------------------------------------------------------------------------- #
# Export
# --------------------------------------------------------------------------- #


def test_render_csv_has_header_and_rows():
    e1 = Entry.create(kind="medication", pet="Rex", name="Flea", date_value="2026-10-01", next_due="2026-10-15")
    e1.id = 1
    csv_text = render_csv([e1])
    lines = csv_text.strip().splitlines()
    assert lines[0].startswith("id,kind,pet,name,date")
    assert any("Flea" in line for line in lines)


def test_render_csv_sorted_by_date():
    e2 = Entry.create(kind="note", pet="Rex", name="B", date_value="2026-10-05"); e2.id = 2
    e1 = Entry.create(kind="note", pet="Rex", name="A", date_value="2026-10-01"); e1.id = 1
    csv_text = render_csv([e2, e1])
    lines = [l for l in csv_text.strip().splitlines() if l and not l.startswith("id,")]
    assert lines[0].split(",")[4] == "2026-10-01"
    assert lines[1].split(",")[4] == "2026-10-05"


def test_render_care_sheet_contains_pet_and_kind():
    e = Entry.create(kind="medication", pet="Rex", name="Flea", date_value="2026-10-01", details=" oral", next_due="2026-10-15")
    sheet = render_care_sheet([e])
    assert "PET CARE SHEET" in sheet
    assert "MEDICATION" in sheet
    assert "Flea" in sheet
    assert "2026-10-15" in sheet


def test_render_care_sheet_filters_by_pet():
    e1 = Entry.create(kind="medication", pet="Rex", name="A", date_value="2026-10-01")
    e2 = Entry.create(kind="medication", pet="Milo", name="B", date_value="2026-10-01")
    sheet = render_care_sheet([e1, e2], pet="Rex")
    assert "Rex" in sheet
    assert "Milo" not in sheet


def test_render_care_sheet_empty():
    sheet = render_care_sheet([])
    assert "no records" in sheet.lower()


def test_due_entries(tmp_path: Path):
    store = Storage(tmp_path / "r.json")
    today_ = today()
    store.add(Entry.create(kind="medication", pet="Rex", name="A", date_value=today_.isoformat(), next_due=(today_ + timedelta(days=3)).isoformat()))
    store.add(Entry.create(kind="medication", pet="Rex", name="B", date_value=today_.isoformat(), next_due=(today_ + timedelta(days=-2)).isoformat()))
    due_now = [e for e in store.all() if e.is_due()]
    assert len(due_now) == 1
    assert due_now[0].name == "B"