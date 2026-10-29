# pet-care-record-cli

A small, local-first command-line tool for logging pet medications, vet visits,
vaccinations, and care notes. All data stays in a JSON file on your machine —
nothing is sent anywhere, and no API keys are needed.

Built by **Asdale Dynamics, LLC** as a practical, beginner-friendly utility.

## Features

- Log four kinds of records: `medication`, `vet_visit`, `vaccination`, `note`
- Local JSON storage (default `~/.petcare/records.json`)
- CSV export for spreadsheets or bookkeeping
- Printable plain-text care sheets for pet sitters
- Upcoming-due-date listing
- Pure Python, no network access, no secrets

## Installation

```bash
pip install -e .
```

This installs the `petcare` command on your PATH.

## Quick start

```bash
# Add a medication
petcare add medication Rex "Flea treatment" 2026-10-01 \
  --details "Give with food" --next-due 2026-10-15

# Add a vet visit
petcare add vet_visit Rex "Annual checkup" 2026-10-10 \
  --details "Vet: Dr. Lee, weight 22kg"

# Add a vaccination
petcare add vaccination Rex "Rabies" 2026-09-01 --next-due 2027-09-01

# Add a care note
petcare add note Rex "Walked 30 min" 2026-10-11 --details "Morning, sunny"

# List everything
petcare list

# Show upcoming due dates
petcare due

# Export to CSV
petcare export care.csv

# Print a care sheet for a sitter
petcare sheet sitter-sheet.txt --pet Rex
```

## Commands

| Command | Description |
| --- | --- |
| `add <kind> <pet> <name> <date>` | Add a care entry |
| `list` | List all entries |
| `due` | Show entries with upcoming due dates |
| `export <path>` | Write entries to CSV |
| `sheet <path>` | Write a printable care sheet |

Use `--data <path>` on any command to point at a different JSON file.

## Storage

Records are stored as a JSON array in `~/.petcare/records.json` by default.
Pass `--data /path/to/records.json` to use a different file (useful for
per-pet or per-household files). Writes are atomic: a crash mid-write cannot
corrupt the previous data.

## Development

```bash
pip install -e .
pytest
```

## License

[MIT](LICENSE) — Copyright (c) 2026 Asdale Dynamics, LLC