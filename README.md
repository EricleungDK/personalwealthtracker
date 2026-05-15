# PersonalWorthTracker

Local-first automation for a personal wealth tracker workbook. The MVP reads a Nordea bank statement, categorizes transactions with deterministic rules, maps category totals into the existing Excel tracker structure, and produces review/audit outputs before anything is written.

## Status

MVP 1 is scaffolded as a Python project. It is intentionally local-only:

- Preferred bank cashflow input: Nordea CSV export.
- Fallback/legacy bank cashflow input: Nordea `Kontoudskrift` PDF with embedded text.
- Tracker workbook: existing Excel file with sheet `Net worth`.
- Currency policy: DKK.
- Default mode: dry-run.
- Commit mode: writes only to a copied workbook under `data/processed/`.
- Deferred: Google Drive, bank APIs, scheduler, notifications, budget alerts, and LLM categorization.

Nordea CSV is the preferred bank cashflow input because it includes merchant-rich fields that improve deterministic categorization. PDF remains supported as a fallback/legacy input for older statement workflows.

## Privacy

This project handles sensitive personal finance data. Real statements, tracker workbooks, generated reports, backups, logs, credentials, PDFs, CSVs, and XLSX files are ignored by `.gitignore`.

`bank-statement.pdf`, local Nordea CSV exports, and `Net Worth Tracker.xlsx` are local reference files and should not be committed. Parser tests should use only redacted or synthetic fixtures, named like `tests/fixtures/nordea_account_statement.redacted.pdf` or `tests/fixtures/nordea_transactions.redacted.csv`.

Real CSV exports are ignored by Git and must not be committed. Keep them under an ignored local path such as `data/raw_statements/` or pass any other ignored local path to `--statement`.

Private merchant-specific categorization belongs in `config/rules.local.yaml`, which is ignored by Git. Start from `config/rules.local.example.yaml` when adding local historical mappings, keyword rules, or recurring amount/date rules.

The committed Nordea PDF fixture is synthetic and redacted. Regenerate it with:

```bash
.venv/bin/python scripts/generate_redacted_nordea_fixture.py
```

## Setup

This workspace is pinned to Python 3.12 through `.python-version`.

```bash
uv sync --extra dev
```

## CSV-First Dry Run

Use Nordea CSV for normal bank cashflow categorization. In `auto` mode the CLI routes `.csv` statements to the Nordea CSV parser:

```bash
uv run wealth-tracker \
  --tracker "Net Worth Tracker.xlsx" \
  --statement "data/raw_statements/ignored-nordea-export.csv" \
  --statement-format auto \
  --year 2026 \
  --month Apr
```

You can also choose CSV parsing explicitly:

```bash
uv run wealth-tracker \
  --tracker "Net Worth Tracker.xlsx" \
  --statement "data/raw_statements/ignored-nordea-export.csv" \
  --statement-format nordea-csv \
  --year 2026 \
  --month Apr
```

For local smoke validation, run one dry-run against a real ignored CSV export and inspect the generated report, categorized CSV, review CSV, and audit log under `reports/`. The command must not require moving the real CSV into a committed fixture path. Do not commit real CSV input or generated report/audit outputs.

Investment statements remain separate future PDF evidence. Bank CSV and PDF inputs prove cashflow; future investment account statements should prove month-end asset values or holdings through a separate evidence contract and are not routed through the bank cashflow parser.

## PDF Fallback Dry Run

```bash
uv run wealth-tracker \
  --tracker "Net Worth Tracker.xlsx" \
  --statement "bank-statement.pdf" \
  --statement-format nordea-pdf \
  --year 2026 \
  --month Apr
```

Dry-run parses the statement, categorizes transactions, resolves workbook target cells, and writes local outputs under `reports/`. It does not modify the workbook.

The run fails before categorization if the Nordea statement currency is not DKK or if any parsed transaction falls outside the requested `--year`/`--month`.

## Commit Mode

```bash
uv run wealth-tracker \
  --tracker "Net Worth Tracker.xlsx" \
  --statement "data/raw_statements/ignored-nordea-export.csv" \
  --statement-format auto \
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
