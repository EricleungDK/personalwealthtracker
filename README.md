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
- Optional: local Ollama/Gemma review suggestions with explicit `--local-llm-suggestions`.
- Deferred: Google Drive, bank APIs, scheduler, notifications, budget alerts, and remote or auto-write LLM categorization.

Nordea CSV is the preferred bank cashflow input because it includes merchant-rich fields that improve deterministic categorization. PDF remains supported as a fallback/legacy input for older statement workflows.

## Privacy

This project handles sensitive personal finance data. Real statements, tracker workbooks, generated reports, backups, logs, credentials, PDFs, CSVs, and XLSX files are ignored by `.gitignore`.

The public/private boundary is documented in [docs/public_private_boundary.md](docs/public_private_boundary.md). Public package artifacts are reusable code, synthetic fixtures, sample config, and docs. Private profile artifacts are real statements, tracker workbooks, generated outputs, Category Memory, Importer Profiles, local rules, proxy split rules, and local profile paths.

`bank-statement.pdf`, local Nordea CSV exports, and `Net Worth Tracker.xlsx` are local reference files and should not be committed. Parser tests should use only redacted or synthetic fixtures, named like `tests/fixtures/nordea_account_statement.redacted.pdf` or `tests/fixtures/nordea_transactions.redacted.csv`.

Real CSV exports are ignored by Git and must not be committed. Keep them under an ignored local path such as `data/raw_statements/` or pass any other ignored local path to `--statement`.

Private merchant-specific categorization belongs in `config/rules.local.yaml`, which is ignored by Git. Start from `config/rules.local.example.yaml` when adding local historical mappings, keyword rules, or recurring amount/date rules.

Local profile files belong under ignored paths such as `profiles/default.local.yaml`. Start from `config/profile.example.yaml` when documenting local tracker workbook paths, statement folders, report folders, Category Memory, Importer Profiles, and local rule overlays.

The committed Nordea PDF fixture is synthetic and redacted. Regenerate it with:

```bash
.venv/bin/python scripts/generate_redacted_nordea_fixture.py
```

## Setup

This workspace is pinned to Python 3.12 through `.python-version`.

```bash
uv sync --extra dev
```

Initialize a local public-template workspace:

```bash
uv run wealth-tracker setup \
  --workspace "local-wealth-workspace" \
  --tracker-currency DKK \
  --start-year 2026
```

Setup creates local `config/`, `profiles/`, `templates/`, `examples/`, `data/`, `reports/`, and `logs/` paths; generates `templates/local-wealth-tracker-template.xlsx`; writes generic sample config/profile files; and adds a synthetic Nordea CSV example. Existing setup-managed files are preserved unless `--force` is supplied.

## Documentation

- [docs/project_overview.md](docs/project_overview.md) is the plain-language project map with Mermaid diagrams for structure, monthly flow, components, outputs, scripts, and terms.
- [docs/public_package_workflow.md](docs/public_package_workflow.md) is the Public Package Workflow for setup, synthetic examples, trusted imports, unknown-format review, learning, and commit-to-copy runs.
- [docs/monthly_workflow.md](docs/monthly_workflow.md) is the monthly operator checklist.
- [docs/public_private_boundary.md](docs/public_private_boundary.md) defines the public/private boundary for future package work.
- [docs/template_workbook.md](docs/template_workbook.md) documents the versioned synthetic Template Workbook contract.
- `.agent/System/` contains deeper architecture and data-contract notes for coding agents.

## Template Workbook

Generate the public synthetic Template Workbook locally:

```bash
uv run wealth-tracker template-workbook create \
  --output "templates/local-wealth-tracker-template.xlsx" \
  --tracker-currency DKK \
  --start-year 2026
```

The generated workbook contains a hidden `Template Metadata` sheet with `template_id`, `template_version`, `workbook_kind`, `tracker_currency`, and `template_schema`. It uses generic rows and formulas only; do not replace it with a private tracker workbook or committed real financial values.

Customize supported v1 labels and currency only through the template command:

```bash
uv run wealth-tracker template-workbook customize \
  --template "templates/local-wealth-tracker-template.xlsx" \
  --output "templates/local-wealth-tracker-template-custom.xlsx" \
  --tracker-currency EUR \
  --rename "Groceries (monthly)=Groceries"
```

Unsupported formula changes, arbitrary layout edits, missing metadata, and unsupported template versions are rejected instead of repaired automatically.

## CSV-First Dry Run

For the full monthly operator checklist, see [docs/monthly_workflow.md](docs/monthly_workflow.md).

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

## Local LLM Review Suggestions

Local LLM Mode is optional; a single model answer is review-only. Add `--local-llm-suggestions` to ask two local models for local Ollama/Gemma review suggestions on unmatched transactions and low-confidence review rows:

```bash
uv run wealth-tracker \
  --tracker "Net Worth Tracker.xlsx" \
  --statement "data/raw_statements/ignored-nordea-export.csv" \
  --statement-format auto \
  --year 2026 \
  --month Apr \
  --local-llm-suggestions
```

Two local models vote on each row: `gemma4:26b` then `gemma4:12b`, with installed `qwen3:14b` as fallback and a 180-second cold-start provider timeout. When both pick the same leaf, the amount is at most 1000 DKK and the leaf is not never-auto, the row is `auto`; otherwise it stays in review with the suggestion and alternatives. Suggestions reuse the existing review workbook fields and never create categories or learn Category Memory unless you confirm the row in the reviewed workbook. Low-confidence category responses are ignored and reported so weak guesses stay in ordinary manual review.

When `learn-category-memory` imports rows with `learn_to_memory=yes`, it also updates the private editable policy file `data/category_memory/reviewed_policy.local.md`. Future Local LLM prompts can use that file as review guidance, while exact repeated merchant matches still come from deterministic Category Memory first.

## Unknown Statement Import Review

Unknown statement formats can be turned into an untrusted review artifact without feeding monthly planning:

```bash
uv run wealth-tracker import-statement \
  --statement "data/raw_statements/unknown-export.txt" \
  --year 2026 \
  --month Apr
```

This writes `untrusted_import_review_<year>_<month>.csv` under `reports/`. Every row is review-required and ineligible for workbook writes until a later confirmed-import workflow promotes reviewed data.

After manually confirming rows in the review CSV, a private Importer Profile can be learned locally:

```bash
uv run wealth-tracker importer-profile learn \
  --reviewed-import "reports/untrusted_import_review_2026_apr.csv" \
  --profile-name synthetic-bank
```

Importer Profiles live under ignored `data/importer_profiles/` by default. Export one only by explicit command:

```bash
uv run wealth-tracker importer-profile export \
  --profile-name synthetic-bank \
  --output "exports/synthetic-bank.importer_profile.json"
```

Use a local Importer Profile during a later unknown import to surface Educated Import Guesses:

```bash
uv run wealth-tracker import-statement \
  --statement "data/raw_statements/unknown-export.txt" \
  --year 2026 \
  --month Apr \
  --importer-profile synthetic-bank
```

Guesses appear in the review CSV as `suggested_category`, `guess_state`, `guess_confidence`, `guess_reason`, and `guess_profile`. They remain review-only; use `confirmed` and `confirmed_category` to accept or correct rows later.

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
├── docs/                   - User-facing workflow and project overview docs
├── src/personal_wealth_tracker/
│   ├── cli.py              - Command-line interface
│   ├── pipeline.py         - End-to-end orchestration
│   ├── nordea_csv.py       - Preferred Nordea CSV statement parser
│   ├── nordea_pdf.py       - Nordea PDF statement parser
│   ├── categorizer.py      - Historical and keyword categorization
│   ├── category_memory.py  - Private learned category decisions
│   ├── review_decisions.py - Reviewed XLSX/CSV monthly decision import
│   ├── workbook.py         - Excel planning and safe commit writer
│   ├── reporting.py        - Markdown, CSV, JSONL, and XLSX outputs
│   └── cleanup.py          - Separate workbook maintenance commands
├── scripts/                - Helper utilities for safe test fixtures
├── tests/                  - Unit and integration tests
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
