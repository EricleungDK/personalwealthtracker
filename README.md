# PersonalWorthTracker

Local-first automation for a personal wealth tracker workbook. The MVP reads a Nordea PDF account statement, categorizes transactions with deterministic rules, maps category totals into the existing Excel tracker structure, and produces review/audit outputs before anything is written.

## Status

MVP 1 is scaffolded as a Python project. It is intentionally local-only:

- Input statement: Nordea `Kontoudskrift` PDF with embedded text.
- Tracker workbook: existing Excel file with sheet `Net worth`.
- Currency policy: DKK.
- Default mode: dry-run.
- Commit mode: writes only to a copied workbook under `data/processed/`.
- Deferred: Google Drive, bank APIs, scheduler, notifications, budget alerts, and LLM categorization.

## Privacy

This project handles sensitive personal finance data. Real statements, tracker workbooks, generated reports, backups, logs, credentials, PDFs, CSVs, and XLSX files are ignored by `.gitignore`.

`bank-statement.pdf` and `Net Worth Tracker.xlsx` are local reference files and should not be committed. Parser tests should use only redacted fixtures, named like `tests/fixtures/nordea_account_statement.redacted.pdf`.

## Setup

This workspace is pinned to Python 3.12 through `.python-version`.

```bash
uv sync --extra dev
```

## Dry Run

```bash
uv run wealth-tracker \
  --tracker "Net Worth Tracker.xlsx" \
  --statement "bank-statement.pdf" \
  --year 2026 \
  --month Apr
```

Dry-run parses the statement, categorizes transactions, resolves workbook target cells, and writes local outputs under `reports/`. It does not modify the workbook.

## Commit Mode

```bash
uv run wealth-tracker \
  --tracker "Net Worth Tracker.xlsx" \
  --statement "bank-statement.pdf" \
  --year 2026 \
  --month Apr \
  --commit
```

Commit mode creates a backup under `data/backups/` and writes eligible updates only to a copied workbook under `data/processed/`. It skips formulas, fixed rows, populated manual cells, unknown categories, and review-required transactions.

## Project Structure

```text
.
├── config/                 - Category, rule, and runtime configuration
├── src/personal_wealth_tracker/
│   ├── cli.py              - Command-line interface
│   ├── pipeline.py         - End-to-end orchestration
│   ├── nordea_pdf.py       - Nordea PDF statement parser
│   ├── categorizer.py      - Historical and keyword categorization
│   ├── workbook.py         - Excel planning and safe commit writer
│   └── reporting.py        - Markdown, CSV, and JSONL outputs
├── tests/                  - Unit tests
└── .agent/System/          - Durable project architecture and contracts
```

## Validation

```bash
uv run pytest
```

If dependencies are not installed yet, static compilation can still be checked with:

```bash
python3 -m compileall src tests
```

In sandboxed shells where `uv run` cannot access its global cache, use the project virtualenv directly after `uv sync`:

```bash
.venv/bin/pytest
```
