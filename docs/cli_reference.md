# CLI Reference

Every `wealth-tracker` command, flag and output in one place. For the short version see the [README](../README.md); for the month-end checklist see [docs/monthly_workflow.md](monthly_workflow.md).

Nordea CSV is the preferred bank cashflow input because it includes merchant-rich fields that improve deterministic categorization. PDF remains supported as a fallback/legacy input for older statement workflows.

Real CSV exports are ignored by Git and must not be committed. Keep them under an ignored local path such as `data/raw_statements/` or pass any other ignored local path to `--statement`.

All default paths are relative to the directory you run the command from. For `monthly` and the per-month command, path defaults come from the profile's `profile_paths` first (`--profile`, default `profiles/default.local.yaml` when it exists; its paths are relative to the workspace that holds `profiles/`); an explicit flag always wins.

## Command Summary

| Command | Flags (default) |
| --- | --- |
| `setup` | `--workspace` (`.`), `--tracker-currency` (`DKK`), `--start-year` (`2026`), `--force`, `--reports-dir`, `--category-memory-dir`, `--importer-profiles-dir` |
| `monthly` | `--tracker` (`Net Worth Tracker.xlsx`), `--statements-dir` (`data/raw_statements`), `--config-dir` (`config`), `--profile`, `--output-dir` (`reports`), `--category-memory-dir` (`data/category_memory`), `--backups-dir` (`data/backups`), `--processed-dir` (`data/processed`), `--dry-run` |
| per-month (no subcommand) | required `--tracker`, `--statement`, `--year`, `--month`; `--statement-format` (`auto` \| `nordea-csv` \| `nordea-pdf`), `--config-dir`, `--profile`, `--output-dir`, `--category-memory-dir`, `--backups-dir`, `--processed-dir` (as `monthly`), `--review-decisions`, `--local-llm-suggestions`, `--commit` |
| `learn-category-memory` | required `--decisions`; `--memory-dir` (`data/category_memory`), `--config-dir` (`config`) |
| `cleanup-currency-labels` | required `--tracker`; `--tracker-currency` (`DKK`), `--output-dir` (`reports`), `--commit` |
| `import-statement` | required `--statement`, `--year`, `--month`; `--tracker-currency` (`DKK`), `--output-dir` (`reports`), `--local-model`, `--importer-profiles-dir` (`data/importer_profiles`), `--importer-profile` |
| `importer-profile learn` | required `--reviewed-import`, `--profile-name`; `--profiles-dir` (`data/importer_profiles`), `--tracker-currency` (`DKK`) |
| `importer-profile export` | required `--profile-name`, `--output`; `--profiles-dir` |
| `importer-profile reset` | required `--profile-name`; `--profiles-dir` |
| `template-workbook create` | required `--output`; `--tracker-currency` (`DKK`), `--start-year` (`2026`), `--sheet-name` (`Net worth`) |
| `template-workbook customize` | required `--template`, `--output`; `--tracker-currency`, `--rename OLD=NEW` (repeatable) |

The per-month command and `cleanup-currency-labels` are dry runs unless `--commit` is given; `monthly` commits by default (only when nothing is in review) and `--dry-run` previews. `uv run wealth-tracker <command> --help` prints one command's flags; plain `wealth-tracker --help` shows the per-month command's flags plus the list of subcommands.

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

## Monthly Command

```bash
uv run wealth-tracker monthly
uv run wealth-tracker monthly --dry-run
```

`monthly` takes the newest CSV in `data/raw_statements/`, infers the month from its row dates, and runs categorisation, the two local model voters and the Trust Policy against `Net Worth Tracker.xlsx`. With zero rows in review it commits the month to a copied workbook; otherwise it writes the Exception Sheet `reports/review_required_<year>_<mon>.xlsx` and stops. Fill and save that sheet (blank accepts the suggestion, `NONE` rejects; a row without a suggestion needs a category or `NONE`) and re-run `monthly`; each run rewrites that one sheet with your decisions kept and the rows still open listed first, until the month commits. Blank rows in a sheet unchanged since the tool wrote it are not accepted. The summary prints auto rows, rows in review, pending amount and the next action. `--dry-run` writes the Exception Sheet and Audit preview but never the workbook, backup, Category Memory or category registry (new leaf requests are only listed in the report). Without a running local model the run still completes; unmatched rows become exceptions. Override paths with `--tracker`, `--statements-dir`, `--config-dir`, `--output-dir` and `--category-memory-dir`.

## Per-Month Command: CSV-First Dry Run

For the full monthly operator checklist, see [docs/monthly_workflow.md](monthly_workflow.md).

`monthly` covers the normal case. The per-month command (no subcommand) is for an older month, a PDF, or an explicit `--year`/`--month`. Use Nordea CSV for normal bank cashflow categorization. In `auto` mode the CLI routes `.csv` statements to the Nordea CSV parser:

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

Local LLM Mode is optional; a single model answer is review-only. `monthly` always asks the local models; on the per-month command add `--local-llm-suggestions` to ask two local Ollama models about unmatched transactions and low-confidence review rows:

```bash
uv run wealth-tracker \
  --tracker "Net Worth Tracker.xlsx" \
  --statement "data/raw_statements/ignored-nordea-export.csv" \
  --statement-format auto \
  --year 2026 \
  --month Apr \
  --local-llm-suggestions
```

Two local models vote on each row: `gemma4:26b` then `gemma4:12b`, with installed `qwen3:14b` as fallback and a 180-second cold-start provider timeout. When both pick the same leaf, the amount is at most 1000 DKK and the leaf is not never-auto, the row is `auto`; otherwise it stays in review with the suggestion and alternatives. Suggestions fill the Exception Sheet's `suggested_category` and dropdown alternatives; they never create categories themselves (a proposed new leaf waits for your decision). Low-confidence category responses are ignored and reported so weak guesses stay in ordinary manual review.

Committing a month (`monthly`, or the per-month command with `--commit`) learns Category Memory: your decisions as `human`, consensus results as `auto` (used only after two consistent committed months, a Suggester hint before that). Learning also updates the private editable policy file `data/category_memory/reviewed_policy.local.md`. Future Local LLM prompts can use that file as review guidance, while exact repeated merchant matches still come from deterministic Category Memory first.

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

The run fails before categorization if the Nordea statement currency differs from `statement.currency` in `config/settings.yaml` (DKK by default; it must equal `tracker.currency`) or if any parsed transaction falls outside the requested `--year`/`--month`.

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

Commit mode is an Atomic Month Commit: when any row is still in review it writes no workbook and leaves the Exception Sheet (`review_required_<year>_<mon>.xlsx`, e.g. `review_required_2026_apr.xlsx`); fill it and re-run with `--review-decisions` pointing at it to commit. The per-month command then writes its refreshed sheet to `review_required_<year>_<mon>_after_decisions.xlsx` instead of overwriting yours. With zero rows in review it creates a backup under `data/backups/` (`--backups-dir`), writes the month only to a copied workbook under `data/processed/` (`--processed-dir`) (skipping formulas and fixed rows), adds any new leaves to `config/categories.yaml`, and learns Category Memory.

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
│   ├── statement_adapters.py - Trusted statement routing and one-month validation
│   ├── categorizer.py      - Memory, Guidance Alias, historical and keyword categorization
│   ├── category_memory.py  - Private learned category decisions
│   ├── suggester.py        - Local model suggestions (Consensus of two voters)
│   ├── local_llm.py        - Ollama client and prompt building
│   ├── trust_policy.py     - Per-row auto/review authority
│   ├── review_decisions.py - Reviewed XLSX/CSV monthly decision import
│   ├── workbook.py         - Excel planning and safe commit writer
│   ├── row_insertion.py    - Formula-aware new leaf row insertion
│   ├── reporting.py        - Markdown, CSV, JSONL, and XLSX outputs
│   ├── cleanup.py          - Separate workbook maintenance commands
│   └── setup_workspace.py, template_workbook.py, statement_import_assistant.py, importer_profiles.py
│                           - Setup, Template Workbook, unknown-format import
├── scripts/                - Helper utilities for safe test fixtures
├── tests/                  - Unit and integration tests
└── .agent/System/          - Durable project architecture and contracts
```


## Validation

```bash
uv run pytest
```

In sandboxed shells where `uv run` cannot access its global cache, use the project virtualenv directly after `uv sync`:

```bash
.venv/bin/pytest
```
