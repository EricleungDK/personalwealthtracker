# Public Package Workflow

This guide is the public-package path for using PersonalWorthTracker without private financial data. It shows the install, setup, synthetic examples, trusted imports, unknown-format review flow, learning, and in-place workbook commit path.

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

The setup command creates generic config, a private local profile, ignored local data folders, reports and logs folders, the versioned synthetic Template Workbook at `templates/local-wealth-tracker-template.xlsx`, and the synthetic statement example at `examples/synthetic-nordea-transactions.csv`.

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

## Run A Trusted Statement Import

Known statement formats go through a Trusted Statement Adapter. Today the public trusted cashflow path is Nordea CSV, with Nordea PDF kept as a fallback/legacy adapter.

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

Use the generated `review_required_<year>_<month>.xlsx` or CSV to confirm rows that need human attention. Current-month decisions can be imported back into a later run, and future merchant choices can be learned only after review.

Committing a month learns its decisions into private Category Memory. To import confirmed decisions by hand instead:

```bash
uv run wealth-tracker learn-category-memory \
  --reviewed-decisions "reports/review_required_2026_apr.xlsx"
```

Category Memory is local profile state. It is not a public fixture and must not be committed.

## Commit To The Workbook

After dry-run review, use `--commit` to write only eligible values into the workbook:

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

Local model integration is optional and review-only. Use `--local-llm-suggestions` to request local Ollama/Gemma hints for unmatched or low-confidence rows. Model output is written into review suggestion fields and never writes workbook values, creates categories, or learns memory without user review.

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
