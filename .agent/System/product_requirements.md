# Product Requirements

Last updated: 2026-09-27

## Goal

Build a local-first automation helper that reduces monthly manual entry in the existing personal wealth tracker workbook while keeping the workbook as the source of truth.

The product is a monthly tracker workbook updater, not a personal finance ledger. It proposes safe monthly updates from statement evidence, produces review artifacts, learns only from explicit review decisions, and writes into the tracker workbook only after a backup.

## Current MVP Scope

- Run as a Python CLI (`wealth-tracker`, package `personal-wealth-tracker`) managed by `uv` and `pyproject.toml`.
- Provide one-command month-end processing with `wealth-tracker monthly` (newest CSV, inferred month, `--dry-run` preview); keep the per-month flags command for explicit paths and PDF input.
- Use Nordea CSV exports as the preferred bank cashflow input.
- Keep Nordea `Kontoudskrift` PDFs with embedded text as fallback/legacy input.
- Treat DKK as the tracker currency for bank cashflow runs.
- Route statement parsing with `--statement-format auto`, `nordea-csv`, or `nordea-pdf`.
- Normalize transaction dates, descriptions, DKK amounts, direction, balances, source metadata, and deterministic transaction IDs.
- Categorize transactions with Category Memory, Guidance Aliases, historical rules, recurring amount/date rules, keyword rules, reviewed monthly decisions, local two-model Consensus suggestions, and explicit unmatched review paths.
- Decide per-row `auto`/`review` authority with one Trust Policy (amount cap, never-auto categories, `min_agreement` model votes, deterministic confidence threshold).
- Use `config/categories.yaml` as the durable YAML category registry for Parent/Section Row, Leaf Category Row, derived row, alias, and allowed-new-child semantics.
- Generate Markdown reports, JSONL audit logs, categorized transaction CSV files, review-required CSV files, and one Exception Sheet XLSX per month (`Review Required` + `Audit`) with decisions carried forward across runs.
- Use the Exception Sheet for `manual_category` (blank accepts the suggestion, `NONE` rejects), `new_parent_category`, `new_leaf_category`, and `learn_to_memory` decisions.
- Apply Monthly Review Decisions from the saved Exception Sheet (`monthly`) or an explicit `--review-decisions` file; an Exception Sheet unchanged since the tool wrote it accepts no blank rows.
- Register validated new leaf categories from reviewed runs in memory before workbook planning; persist them to `config/categories.yaml` only on a successful month commit.
- Learn Category Memory when a month commits: decisions as `human`, consensus results as `auto` trusted after two committed months; targets must be valid leaf categories.
- Keep Category Memory in ignored private local data under `data/category_memory/`.
- Support private local rule overlays in ignored `config/rules.local.yaml`.
- Support private proxy split rules that split one intermediary transfer into allocation lines plus optional residual review lines.
- Plan workbook value updates and structure changes before writing.
- Commit a month atomically: only with zero rows in review, create a backup under `data/backups/`, then write eligible changes into the tracker in place, so months accumulate (ADR 0007).
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
- `learn_to_memory` `no` keeps a committed decision out of memory; the manual import still needs `yes`.
- Category Memory must skip parent rows, derived rows, missing categories, residual proxy split rows, and other non-leaf targets.
- Stale or unknown transaction IDs in reviewed artifacts must fail clearly instead of being guessed.

## Out Of Scope

- Direct writes to the original workbook.
- Google Drive read/write.
- Bank API or Open Banking ingestion.
- Scheduler and monthly notifications.
- LLM categorization as an auto-write source except via two-model local Consensus under the Trust Policy (ADR 0002).
- Hosted (cloud) model judgment; deferred, with outbound redaction and the optional `hosted` extra kept unused (ADR 0005).
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
