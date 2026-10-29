"""Tests for petcare entry logic and date math."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from petcare.models import (
    Entry,
    VALID_KINDS,
    add_days,
    days_between,
    days_until,
    is_due,
    parse_date,
    today,
    validate_kind,
)


# --------------------------------------------------------------------------- #
# Date math
# --------------------------------------------------------------------------- #


def test_parse_date_valid():
    assert parse_date("2026-10-29") == date(2026, 10, 29)


@pytest.mark.parametrize("bad", ["", "2026/10/29", "oct 29 2026", "2026-10-2", "2026-13-40", None, 123])
def test_parse_date_invalid(bad):
    with pytest.raises(ValueError):
        parse_date(bad)


def test_add_days():
    d = date(2026, 1, 31)
    assert add_days(d, 1) == date(2026, 2, 1)
    assert add_days(d, -1) == date(2026, 1, 30)


def test_days_between():
    assert days_between(date(2026, 1, 1), date(2026, 1, 11)) == 10
    assert days_between(date(2026, 1, 11), date(2026, 1, 1)) == -10


def test_days_until_defaults_to_today():
    future = today() + timedelta(days=5)
    assert days_until(future) == 5


def test_days_until_with_reference():
    assert days_until(date(2026, 12, 1), now=date(2026, 11, 1)) == 30


def test_is_due_window():
    d = date(2026, 12, 1)
    assert is_due(d, now=date(2026, 11, 25)) is False
    assert is_due(d, now=date(2026, 12, 1)) is True
    # window allows future dates
    assert is_due(d, now=date(2026, 11, 25), window=10) is True
    assert is_due(d, now=date(2026, 11, 25), window=5) is False


# --------------------------------------------------------------------------- #
# Entry logic
# --------------------------------------------------------------------------- #


def test_entry_create_normalises_kind():
    e = Entry.create(kind="MEDICATION", pet="Rex", name="Flea", date_value="2026-10-01")
    assert e.kind == "medication"


def test_entry_create_rejects_bad_kind():
    with pytest.raises(ValueError):
        Entry.create(kind="bogus", pet="Rex", name="X", date_value="2026-10-01")


def test_entry_create_rejects_bad_date():
    with pytest.raises(ValueError):
        Entry.create(kind="medication", pet="Rex", name="X", date_value="10/01/2026")


def test_entry_create_rejects_bad_next_due():
    with pytest.raises(ValueError):
        Entry.create(
            kind="medication", pet="Rex", name="X", date_value="2026-10-01", next_due="nope"
        )


def test_entry_next_due_math():
    e = Entry.create(
        kind="medication", pet="Rex", name="Flea", date_value="2026-10-01", next_due="2026-10-15"
    )
    assert e.next_due_obj() == date(2026, 10, 15)
    assert e.days_until_due(now=date(2026, 10, 10)) == 5
    assert e.is_due(now=date(2026, 10, 15)) is True
    assert e.is_due(now=date(2026, 10, 10)) is False


def test_entry_without_next_due_is_never_due():
    e = Entry.create(kind="note", pet="Rex", name="Walked", date_value="2026-10-01")
    assert e.next_due_obj() is None
    assert e.days_until_due() is None
    assert e.is_due() is False


def test_entry_roundtrip_dict():
    e = Entry.create(
        kind="vaccination", pet="Rex", name="Rabies", date_value="2026-09-01", next_due="2027-09-01"
    )
    e.id = 42
    d = e.to_dict()
    e2 = Entry.from_dict(d)
    assert e2.kind == e.kind
    assert e2.id == 42
    assert e2.next_due == "2027-09-01"


def test_validate_kind_accepts_all():
    for k in VALID_KINDS:
        assert validate_kind(k) == k


def test_validate_kind_rejects_unknown():
    with pytest.raises(ValueError):
        validate_kind("nope")


def test_summary_contains_key_fields():
    e = Entry.create(
        kind="vet_visit", pet="Rex", name="Checkup", date_value="2026-10-01", details="Annual"
    )
    s = e.summary()
    assert "vet_visit" in s and "Rex" in s and "Checkup" in s and "Annual" in s