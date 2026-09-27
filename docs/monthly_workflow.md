# Monthly Tracker Workflow

Use this runbook to update the tracker workbook for one reporting month. The normal flow is one command, re-run until the month commits.

For a non-technical map of the project structure, components, outputs, scripts, and terminology, see [project_overview.md](project_overview.md). Decisions behind this flow are in `docs/adr/` (0001 per-row authority, 0002 local Consensus, 0003 Exception Sheet and Atomic Month Commit, 0004 memory on commit, 0005 hosted judgment deferred, 0006 formula-aware leaf row insertion).

## 1. Prepare Local Inputs

- Export the Nordea current-account CSV for exactly one month into `data/raw_statements/` (ignored by Git).
- Keep the tracker workbook local as `Net Worth Tracker.xlsx` in the project root, or pass `--tracker`.
- Start Ollama with `gemma4:26b` and `gemma4:12b` pulled (`qwen3:14b` as fallback). The run still works without them; see step 7.
- Do not move real CSV/PDF/XLSX files into `tests/fixtures/` or any committed path.

## 2. Run The Month

```bash
uv run wealth-tracker monthly
```

`monthly`:

- takes the most recently modified CSV in `data/raw_statements/` (by file time, not statement date) and infers the month from its row dates; a CSV spanning several months fails,
- categorises every row (Category Memory, Guidance Aliases from the optional ignored `config/guidance_aliases.local.yaml` (merchant text to leaf; start from `guidance_aliases.local.example.yaml`), rules, then the two local model voters) and lets the Trust Policy (the per-row rule deciding what may be written without you) mark each row `auto` or `review`,
- reads `reports/review_required_<year>_<mon>.xlsx` (e.g. `review_required_2026_apr.xlsx`) as decisions; a sheet unchanged since the tool wrote it counts only its filled cells (blank does not accept) and the next action says `Exception sheet not reviewed yet: <path>`,
- commits the month when zero rows remain in review, otherwise stops,
- rewrites that same sheet every run: your decisions are kept, rows still needing a decision come first, and rows newly in review are added; a sheet it cannot read, or cannot rewrite because it is open in Excel, stops the run with an error before anything is committed and is left untouched,
- prints `Auto rows`, `Rows in review`, `Pending amount`, the report and Exception Sheet paths, and the next action.

Override paths with `--tracker`, `--statements-dir`, `--config-dir`, `--output-dir` and `--category-memory-dir`.

Outputs under `reports/`:

- `report_<year>_<mon>.md` - run summary, `Categorization Quality` (classification rate, no-review rate, method counts), `Local LLM Mode` diagnostics, planned workbook and structure changes.
- `review_required_<year>_<mon>.xlsx` - the Exception Sheet workbook: `Review Required` and `Audit` sheets, plus hidden `Category Options`, `Decision Options` and `Run Metadata` helper sheets (dropdown sources and run period; leave them in place).
- `review_required_<year>_<mon>.xlsx.written` - fingerprint of the sheet as the tool last wrote it; do not edit.
- `review_required_<year>_<mon>.csv`, `categorized_transactions_<year>_<mon>.csv`, `audit_<year>_<mon>.jsonl` - plain inspection and machine-readable audit.

There is one Exception Sheet per month: always edit `review_required_<year>_<mon>.xlsx`. `monthly` never writes `_after_decisions.xlsx`; only the per-month `--review-decisions` command in step 8 does.

## 3. Preview With Dry Run

```bash
uv run wealth-tracker monthly --dry-run
```

Dry run writes the report, Exception Sheet and Audit preview, but never the workbook copy, backup, Category Memory or `config/categories.yaml` (new leaf requests are only listed under `Category Registry Updates` in the report). Its next action says to re-run without `--dry-run` once nothing is in review.

## 4. Work The Exception Sheet

The `Review Required` sheet lists rows in review (`review`-authority transactions and sources of a blocked workbook update), rows without a suggestion first, then by date. After a run that read your decisions, the rows you already decided follow, with your values prefilled.

How to fill the sheet:

1. Read `date`, `description`, `amount`, `suggested_category`, `reason` (ends with the method in brackets) and `confidence`.
2. `manual_category` is the only column most rows need. Its dropdown lists the row's suggestion and model alternatives first, then `NONE`, then every leaf. Blank accepts `suggested_category`. A row with no suggestion must get a category or `NONE`; blank leaves it in review. The header note says the same.
3. `new_parent_category`, `new_leaf_category` and `learn_to_memory` are optional, see below.
4. `blocked` is filled only when the target workbook cell blocks the commit (`<cell>: <reason>`, e.g. a manual value); pick another category, `NONE`, or fix the workbook.
5. Save the file and re-run. The rewritten sheet keeps every decision you made (a blank you accepted now shows the accepted category in `manual_category`) and lists what is still open first; fill those rows in the same file and save again. Change a prefilled cell to revise a decision; decided rows show no `suggested_category`, so clearing one puts the row back in review.

`suggested_parent_category` appears only when a row proposes a new leaf; split columns (`split_role`, `split_rule`, `source_transaction_id`, `allocated_amount`, `residual_amount`) only when the month has proxy split rows. `transaction_id` is a hidden last column that ties each row to the statement; do not edit it.

- Blank `manual_category` accepts `suggested_category`. A blank row without a suggestion stays in review. Save the sheet even when every row stays blank; until saved, blank rows are not accepted (prefilled decisions still apply).
- `NONE` rejects the suggestion: the row is resolved but written to no category.
- Any other value must be an existing Leaf Category Row, such as `Food& Drinks (monthly)` or `Apple Cloud`. Parent/Section Row labels such as `Living expenses`, `Services` and `Insurance` group the tracker and are not valid targets.
- A proposed subscription leaf (`suggested_parent_category` `Services`, e.g. `Claude subscription`) is always in review. Blank accepts it as a new leaf under `Services` on the commit run (never on `--dry-run`); from the next month Category Memory files the merchant there. Pick an existing leaf such as `Disney+` in `manual_category` or fill `new_parent_category` `Services` and an edited name in `new_leaf_category` instead if it fits better.
- For a missing leaf, pick the allowed Parent/Section Row in `new_parent_category` and type the new label in `new_leaf_category`; leave `manual_category` empty on that row. The run plans it in memory (reported under `Category Registry Updates`); only a commit that writes the workbook adds it to `config/categories.yaml`, as a `- label:` and `description:` pair under the parent with every other line untouched (description `<Service> subscription billing.` for an accepted proposal, `Added in monthly review <Mon YYYY>.` for a typed leaf; edit it to guide the Suggester). A run blocked by rows in review leaves the file unchanged, and re-running with the same sheet adds no duplicate. The commit inserts the row at the end of its parent section in the copied workbook, shifting every formula and expanding the parent SUM in all month columns. If the parent formula is not a simple SUM or the before/after safety check fails, the rows stay in review with the reason and nothing is written.
- `learn_to_memory`: leave blank to learn the decision on commit; `no` for a one-off.
- Use `Category Options` to avoid derived, fixed, or formula-owned rows.
- Use `Audit` to spot-check every `auto` row not in review with its `source`, `votes` and `reason`.

Salary, rent and other `never_auto_categories` rows, rows above `trust_policy.auto_max_amount` (default 1000 DKK), and rows whose cell is blocked (manual value, missing row, several salary deposits) appear every month. Blank accepts them in one pass; a blocked cell needs a different category, `NONE`, or a workbook fix.

Decisions apply by exact `transaction_id` for this reporting month. Stale or unknown IDs fail the run; if the ID scheme changed after a code update, move the old `review_required_<year>_<mon>.xlsx` aside and run `monthly --dry-run` to regenerate it.

## 5. Re-Run To Commit

```bash
uv run wealth-tracker monthly
```

Atomic Month Commit: the copied workbook is written only when zero rows remain in review. Otherwise the report says `Workbook not written: N row(s) in review.` and no backup, workbook copy or Category Memory is written. On commit:

- a backup goes to `data/backups/` and the updated copy to `data/processed/`; the original workbook is untouched,
- formula-owned, fixed, and populated manual cells are never overwritten,
- Category Memory is learned from the month: Exception Sheet decisions and Audit corrections with provenance `human` (used from the next month; `NONE` forgets the merchant's mapping), and Consensus results with provenance `auto`, which categorise only after the same merchant and category commit in two months (a Suggester hint until then).

## 6. Correct A Committed Month

Fill `corrected_category` (a leaf or `NONE`) on the `Audit` sheet of `review_required_<year>_<mon>.xlsx` and re-run `monthly` while that statement is still the newest. The correction becomes a Monthly Review Decision, the month is committed again from the original workbook, and the merchant's memory is replaced with a `human` mapping. For an older month, use the per-month command in step 8 with `--review-decisions` and `--commit`.

## 7. Local LLM Mode And No-Model Degradation

Two local models vote on each row through Ollama's local HTTP API (Consensus): `gemma4:26b` (`model`) first, then `gemma4:12b` (`second_model`). Either voter uses the installed `qwen3:14b` (`fallback_model`) when its model is missing or fails, with a 180-second cold-start provider timeout; `keep_alive` keeps each model warm. Settings live under `local_llm` in `config/settings.yaml`.

A model suggestion reaches `auto` only when both voters pick the same leaf (`trust_policy.min_agreement`, default 2 distinct models), the amount is within `trust_policy.auto_max_amount`, and the leaf is not in `trust_policy.never_auto_categories`. Otherwise it stays review-only, suggesting the primary model's leaf with the other answers as alternatives. The same cap and never-auto list apply to deterministic and memory matches.

Prompt context is minimized: the statement merchant text (raw, so digits like `7-ELEVEN 7060` survive), amount, date, direction, YAML leaf choices with descriptions, Guidance Aliases, and up to five nearest Category Memory neighbours (looked up and shown by normalised merchant identity). raw Nordea descriptions are excluded beyond that merchant text (for Nordea CSV the merchant text is the `Name`/`Title` value itself) unless `include_raw_description: true` is deliberately configured, and then only when they differ from the merchant text. Nothing is sent to a hosted model.

Without a running local model the run still completes: provider failures, timeouts, and invalid or low-confidence answers are recorded in the report's `Local LLM Mode` section and audit log, and the affected rows become ordinary exceptions.

## 8. Per-Month Command (Older Months, PDF Fallback)

`monthly` always uses the newest CSV. For another month, or a PDF when no CSV export exists, run the per-month command. It does not ask the local models unless `--local-llm-suggestions` is given, and it is a dry run unless `--commit` is given. A commit here learns Category Memory and adds new leaves exactly as in step 5; with `--review-decisions` pointing at the month's Exception Sheet, the refreshed sheet is written to `review_required_<year>_<mon>_after_decisions.xlsx`, leaving yours untouched:

```bash
uv run wealth-tracker \
  --tracker "Net Worth Tracker.xlsx" \
  --statement "data/raw_statements/ignored-nordea-export.csv" \
  --statement-format auto \
  --year 2026 \
  --month Apr \
  --local-llm-suggestions \
  --review-decisions "reports/review_required_2026_apr.xlsx" \
  --commit
```

Use `--statement-format nordea-pdf` for a PDF; expect more review because PDFs carry less merchant detail. `--config-dir`, `--output-dir` and `--category-memory-dir` work as for `monthly`.

## 9. Proxy Split Transfer Rows

A Proxy Split Transfer is one bank transfer to an intermediary account used as evidence for several tracker allocations. Personal split rules belong in ignored `config/rules.local.yaml`.

For the Revolut family-transfer pattern, the configured fixed allocation is `8000 * 0.82 = 6560 DKK` for `Parent A` and `4000 * 0.82 = 3280 DKK` for `Parent B`; a matching Revolut expense must cover the full `9840 DKK` before it is split. Methods in the outputs:

- `proxy_split_source`: the original transfer, kept for audit and excluded from workbook totals.
- `proxy_split_allocation`: a counted fixed allocation such as `Parent A` or `Parent B`.
- `proxy_split_residual`: a Residual Review Line for the leftover of a larger transfer.
- `proxy_split_blocked`: a candidate kept review-only because it was underfunded or exceeded the rule's `monthly_limit`.

Residual decisions apply only to the current month and are not learned into Category Memory.

Review Required column order keeps transaction context and the decision first, with split metadata (`split_role`, `split_rule`, `source_transaction_id`, `allocated_amount`, `residual_amount`) after `blocked`, shown only when split rows exist (the `Audit` sheet does the same).

## 10. Manual Memory Import (Escape Hatch)

Memory is learned on commit, so this is normally unused. To learn rows with `learn_to_memory` `yes` without committing:

```bash
uv run wealth-tracker learn-category-memory \
  --decisions "reports/review_required_2026_apr.xlsx" \
  --config-dir config
```

It writes `human` entries, validated against the YAML leaf registry, and refreshes `data/category_memory/reviewed_policy.local.md` (the `## Manual Guidance` section is preserved).

## 11. Separate Maintenance Tasks

Workbook cleanup is not part of the monthly run:

```bash
uv run wealth-tracker cleanup-currency-labels \
  --tracker "Net Worth Tracker.xlsx" \
  --output-dir reports
```

Add `--commit` only to write the cleanup to a copied workbook.

## 12. Privacy Rules

- Do not commit real bank statements, CSV exports, tracker workbooks, generated reports, backups, logs, or category memory.
- Use real CSV exports only for local smoke validation.
- Committed CSV fixtures must be synthetic or redacted.
- Investment statements remain separate future PDF evidence and are not part of this bank cashflow workflow.
