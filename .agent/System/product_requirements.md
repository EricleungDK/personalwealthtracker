# Product Requirements

Last updated: 2026-05-21

## Goal

Build a local-first automation helper that reduces monthly manual entry in the existing personal wealth tracker workbook while keeping the workbook as the source of truth.

The product is a monthly tracker workbook updater, not a personal finance ledger. It proposes safe monthly updates from statement evidence, produces review artifacts, learns only from explicit review decisions, and writes only to copied workbooks.

## Current MVP Scope

- Run as a Python CLI managed by `uv` and `pyproject.toml`.
- Use Nordea CSV exports as the preferred bank cashflow input.
- Keep Nordea `Kontoudskrift` PDFs with embedded text as fallback/legacy input.
- Treat DKK as the tracker currency for bank cashflow runs.
- Route statement parsing with `--statement-format auto`, `nordea-csv`, or `nordea-pdf`.
- Normalize transaction dates, descriptions, DKK amounts, direction, balances, source metadata, and deterministic transaction IDs.
- Categorize transactions with Category Memory, historical rules, recurring amount/date rules, keyword rules, reviewed monthly decisions, and explicit unmatched review paths.
- Use `config/categories.yaml` as the durable YAML category registry for Parent/Section Row, Leaf Category Row, derived row, alias, and allowed-new-child semantics.
- Generate Markdown reports, JSONL audit logs, categorized transaction CSV files, review-required CSV files, and review-required XLSX workbooks.
- Use the review workbook for `manual_category`, `new_parent_category`, `new_leaf_category`, and `learn_to_memory` decisions.
- Apply Monthly Review Decisions only when the operator explicitly supplies `--review-decisions`.
- Register validated new leaf categories from reviewed runs before workbook planning.
- Learn future Category Memory only from explicit `learn_to_memory=yes` decisions that target valid leaf categories.
- Keep Category Memory in ignored private local data under `data/category_memory/`.
- Support private local rule overlays in ignored `config/rules.local.yaml`.
- Support private proxy split rules that split one intermediary transfer into allocation lines plus optional residual review lines.
- Plan workbook value updates and structure changes before writing.
- In commit mode, create backups and write eligible changes only to copied workbooks under `data/processed/`.
- Keep the original tracker workbook unchanged.

## Workbook Safety Requirements

- Locate the existing `Net worth` sheet and the requested reporting period.
- Treat existing manual workbook values as authoritative.
- Never overwrite populated cells, formulas, fixed rows, derived rows, or section total rows.
- Write source-backed values only to valid leaf rows when workbook safety checks pass.
- Preserve workbook formulas, formatting, merged headers, and structure when inserting reviewed leaf rows.
- Report planned workbook structure changes during dry-run before commit mode applies them to a copy.
- Keep currency-label cleanup separate from monthly statement runs.

## Review And Learning Requirements

- The review workbook must keep transaction context and editable review columns close together.
- `manual_category` applies only to the current reporting month.
- `new_parent_category` and `new_leaf_category` request a missing leaf row under an allowed parent.
- `manual_category` and `new_leaf_category` are mutually exclusive for one review row.
- `learn_to_memory` is opt-in; blank or non-yes values must not create future memory.
- Category Memory must skip parent rows, derived rows, missing categories, residual proxy split rows, and other non-leaf targets.
- Stale or unknown transaction IDs in reviewed artifacts must fail clearly instead of being guessed.

## Out Of Scope

- Direct writes to the original workbook.
- Google Drive read/write.
- Bank API or Open Banking ingestion.
- Scheduler and monthly notifications.
- LLM categorization as an auto-write source.
- Generic multi-bank ingestion.
- OCR and scanned PDF parsing.
- Live FX lookup.
- Investment statement ingestion for asset value rows until a separate evidence contract is implemented.
- Crypto or digital asset valuation without a dedicated valuation source.

## Future Requirements

- Investment statement evidence should use a separate valuation contract, not the bank transaction model.
- USD investment values should convert to DKK using a user-maintained fixed rate and record the applied rate in reports/audit logs.
- Combined monthly planning should eventually merge bank cashflow evidence and investment valuation evidence while reporting cross-source mismatches.
- Missing period/year creation should create safe workbook structure only when the existing workbook pattern is unambiguous.
