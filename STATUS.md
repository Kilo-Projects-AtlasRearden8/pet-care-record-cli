# STATUS — pet-care-record-cli

## What was built

A local-first Python CLI (`petcare`) for logging pet medications, vet visits,
vaccinations, and care notes, with local JSON storage and CSV export, plus
printable care sheets for pet sitters.

Layout:

```
pyproject.toml          # setuptools build, `petcare` console script
src/petcare/
  __init__.py
  models.py             # Entry dataclass, date math, kind validation
  storage.py            # atomic JSON store (~/.petcare/records.json by default)
  export.py             # CSV export + printable care sheet renderer
  cli.py                # argparse CLI: add/list/export/sheet/due
tests/
  test_models.py        # entry logic + date math (35 tests total)
  test_storage_export.py
LICENSE                # MIT, Copyright (c) 2026 Asdale Dynamics, LLC
README.md              # credits Asdale Dynamics, LLC
STATUS.md             # this file
```

## How to run

```bash
.venv/bin/pip install -e .          # install (creates `petcare` on PATH)
.venv/bin/petcare add medication Rex "Flea treatment" 2026-10-01 \
    --details "Give with food" --next-due 2026-10-15
.venv/bin/petcare list
.venv/bin/petcare due
.venv/bin/petcare export care.csv
.venv/bin/petcare sheet sitter.txt --pet Rex
```

Use `--data <path>` on any command to point at a different JSON file.

## Verification results

- `pytest` — **35 passed, 0 failed** (date math, entry validation, storage
  crash-tolerance, CSV sorting, care-sheet rendering, due-date logic).
- End-to-end smoke test — `add` (all 4 kinds), `list`, `due`, `export`, and
  `sheet` all produce correct output; JSON is well-formed and IDs increment.
- Error handling — bad dates, bad kinds, and missing subcommands return exit
  code 2 with a clear message; corrupt storage files degrade to empty rather
  than crashing.
- Storage writes are atomic (temp file + rename), so a crash mid-write cannot
  corrupt prior data.

## Known gaps

- No per-user config file; `--data` is the only override. Fine for the
  intended single-user, local-first use.
- `due` only lists future-due items; past-due items are shown in `list` with a
  DUE marker.
- Care sheets are plain-text ASCII, not PDF.
- No import from other formats yet (only JSON round-trip and CSV export).
- Python 3.9+ required; tested on 3.13.