# Public Package Workflow

This guide is the public-package path for using Personal Wealth Tracker without private financial data. It shows the install, setup, the one-command `monthly` run on synthetic examples, the per-month command, the unknown-format review flow, learning, and the in-place workbook commit.

For the privacy contract behind this guide, read the public/private boundary in [public_private_boundary.md](public_private_boundary.md).

## Install

Set up the Python environment with the project development extras:

```bash
uv sync --extra dev
```

The package exposes the `wealth-tracker` command. All examples below use `uv run` so they run inside the local project environment.

## Initialize A Local Workspace

Create a local workspace from public artifacts:

```bash
uv run wealth-tracker setup \
  --workspace "local-wealth-workspace" \
  --tracker-currency DKK \
  --start-year 2026
```

The setup command creates generic config, a private local profile (`profiles/default.local.yaml`; `monthly` and the per-month command read its `profile_paths` as path defaults), ignored local data folders, reports and logs folders, the versioned synthetic Template Workbook at `templates/local-wealth-tracker-template.xlsx`, and the synthetic statement example at `examples/synthetic-nordea-transactions.csv`.

Existing setup-managed files are preserved unless `--force` is supplied. Real statements, real tracker workbooks, local Category Memory, Importer Profile files, report outputs, logs, and local profile files stay private and ignored by Git.

## Use The Template Workbook

The setup workflow creates the public synthetic workbook automatically. You can also generate it directly:

```bash
uv run wealth-tracker template-workbook create \
  --output "templates/local-wealth-tracker-template.xlsx" \
  --tracker-currency DKK \
  --start-year 2026
```

Supported v1 customization is limited to known category or section labels and Tracker Currency:

```bash
uv run wealth-tracker template-workbook customize \
  --template "templates/local-wealth-tracker-template.xlsx" \
  --output "templates/local-wealth-tracker-template-custom.xlsx" \
  --tracker-currency EUR \
  --rename "Groceries (monthly)=Groceries"
```

Formula and layout customization are outside the v1 public contract.

## Run The Month

The normal path is one command, run from inside the workspace. Put the tracker at `Net Worth Tracker.xlsx` and the statement CSV in `data/raw_statements/`:

```bash
cd local-wealth-workspace
cp templates/local-wealth-tracker-template.xlsx "Net Worth Tracker.xlsx"
cp examples/synthetic-nordea-transactions.csv data/raw_statements/
uv run wealth-tracker monthly            # add --dry-run to preview only
```

`monthly` takes the newest CSV, infers its month, and either commits the month into the workbook in place after a backup (when no rows are in review) or writes one Exception Sheet, `reports/review_required_<year>_<mon>.xlsx`. Fill and save it (blank accepts the suggestion, `NONE` rejects) and re-run until it commits. The full checklist is in [monthly_workflow.md](monthly_workflow.md).

## Per-Month Command (Trusted Statement Import)

Known statement formats go through a Trusted Statement Adapter (a parser that validates a known bank format). Today the public trusted cashflow path is Nordea CSV, with Nordea PDF kept as a fallback/legacy adapter. Use the per-month command for an older month or a PDF.

Run the synthetic CSV example against the synthetic workbook:

```bash
uv run wealth-tracker \
  --tracker "templates/local-wealth-tracker-template.xlsx" \
  --statement "examples/synthetic-nordea-transactions.csv" \
  --statement-format auto \
  --year 2026 \
  --month Apr
```

Dry-run writes review artifacts under `reports/` and does not modify the workbook.

## Review And Learn

Fill the generated `review_required_<year>_<mon>.xlsx` Exception Sheet for rows that need human attention, then pass it back with `--review-decisions` (or just re-run `monthly`). Decisions apply by transaction ID to that month only.

Committing a month learns its decisions into private Category Memory, so repeat merchants categorise themselves next month. To import rows marked `learn_to_memory` `yes` by hand without committing:

```bash
uv run wealth-tracker learn-category-memory \
  --decisions "reports/review_required_2026_apr.xlsx"
```

Category Memory is local profile state. It is not a public fixture and must not be committed.

## Commit To The Workbook

After dry-run review, use `--commit` (plus `--review-decisions` if you filled the sheet) to write the month into the workbook. Nothing is written while any row is still in review:

```bash
uv run wealth-tracker \
  --tracker "templates/local-wealth-tracker-template.xlsx" \
  --statement "examples/synthetic-nordea-transactions.csv" \
  --statement-format auto \
  --year 2026 \
  --month Apr \
  --commit
```

Commit mode backs up the workbook to `data/backups/` and then updates it in place, so committed months accumulate. The Commit Ledger `data/commit_ledger.json` lets a re-commit replace only its own earlier values (ADR 0007).

## Unknown Statement Review

Unknown statement formats are handled by the Statement Import Assistant. This path creates untrusted review artifacts; it does not promote rows into trusted monthly planning.

```bash
uv run wealth-tracker import-statement \
  --statement "data/raw_statements/unknown-export.txt" \
  --year 2026 \
  --month Apr
```

After manual review, learn a private Importer Profile:

```bash
uv run wealth-tracker importer-profile learn \
  --reviewed-import "reports/untrusted_import_review_2026_apr.csv" \
  --profile-name synthetic-bank
```

Use the private Importer Profile later for educated guesses:

```bash
uv run wealth-tracker import-statement \
  --statement "data/raw_statements/unknown-export.txt" \
  --year 2026 \
  --month Apr \
  --importer-profile synthetic-bank
```

Importer Profile suggestions remain review-only. They can help a user map columns or categories, but they are not authoritative financial evidence.

## Optional Local Model Assistance

Local model integration is optional and runs only on your machine through Ollama. `monthly` asks two local models automatically; the per-month command asks only with `--local-llm-suggestions`. A model answer is auto-accepted only when both models agree, the amount is at most `trust_policy.auto_max_amount` (default 1000), and the category is not in `trust_policy.never_auto_categories`; otherwise it is a suggestion on the Exception Sheet. Models never create categories. Without a running model, unmatched rows simply go to review.

## Developer Contracts

The public package is designed around a few explicit contracts:

- Trusted Statement Adapter: trusted adapters normalize known formats into validated transaction records with source diagnostics.
- Statement Import Assistant: unknown formats produce untrusted review artifacts only.
- Importer Profile: private local JSON learned from confirmed unknown-import review rows and exported only by explicit command.
- Template Workbook: the public synthetic workbook carries versioned metadata and generic formulas, labels, and sample structure.
- Public/private boundary: package code, docs, sample config, synthetic fixtures, and tests can ship publicly; private statements, workbook copies, reports, Category Memory, Importer Profiles, local rules, profile paths, and generated outputs remain local.

Arbitrary finance workflow support means extensible adapters plus model-assisted review flows, not guaranteed trusted parsing of every financial document.

## V1 Non-Goals

The v1 public package does not include:

- desktop app
- SaaS
- required remote LLMs
- autonomous finance decisions
- direct original-workbook edits
- arbitrary formula/layout editing
- live FX
- bank APIs
- scheduler
- cloud sync
- public shipping of private data
