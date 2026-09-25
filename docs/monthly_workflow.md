# Monthly Tracker Workflow

Use this runbook to update the tracker workbook for one reporting month. The normal flow is one command, re-run until the month commits.

For a non-technical map of the project structure, components, outputs, scripts, and terminology, see [project_overview.md](project_overview.md). Decisions behind this flow are in `docs/adr/` (0001 per-row authority, 0002 local Consensus, 0003 Exception Sheet and Atomic Month Commit, 0004 memory on commit, 0005 hosted judgment deferred).

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
- categorises every row (Category Memory, Guidance Aliases, rules, then the two local model voters) and lets the Trust Policy mark each row `auto` or `review`,
- reuses a filled `reports/review_required_<year>_<mon>.xlsx` (e.g. `review_required_2026_apr.xlsx`) as decisions when it exists,
- commits the month when zero rows remain in review, otherwise writes the Exception Sheet and stops,
- prints `Auto rows`, `Rows in review`, `Pending amount`, the report and Exception Sheet paths, and the next action.

Override paths with `--tracker`, `--statements-dir`, `--config-dir`, `--output-dir` and `--category-memory-dir`.

Outputs under `reports/`:

- `report_<year>_<mon>.md` - run summary, `Categorization Quality` (classification rate, no-review rate, method counts), `Local LLM Mode` diagnostics, planned workbook and structure changes.
- `review_required_<year>_<mon>.xlsx` - the Exception Sheet workbook: `Review Required`, `Audit` and `Category Options` sheets.
- `review_required_<year>_<mon>.csv`, `categorized_transactions_<year>_<mon>.csv`, `audit_<year>_<mon>.jsonl` - plain inspection and machine-readable audit.

When the filled sheet is read back, the follow-up workbook is written as `review_required_<year>_<mon>_after_decisions.xlsx`; keep editing `review_required_<year>_<mon>.xlsx`, which is the file `monthly` reads.

## 3. Preview With Dry Run

```bash
uv run wealth-tracker monthly --dry-run
```

Dry run writes the report, Exception Sheet and Audit preview, but never the workbook copy, backup, Category Memory or `config/categories.yaml` (new leaf requests are only listed under `Category Registry Updates` in the report). Its next action says to re-run without `--dry-run` once nothing is in review.

## 4. Work The Exception Sheet

The `Review Required` sheet lists only rows in review: `review`-authority transactions and sources of a blocked workbook update (see `target_cell` and `workbook_reason`). Each row shows `suggested_category`; the `manual_category` dropdown offers the suggestion, model alternatives, and `NONE`.

- Blank `manual_category` accepts `suggested_category`. A blank row without a suggestion stays in review.
- `NONE` rejects the suggestion: the row is resolved but written to no category.
- Any other value must be an existing Leaf Category Row, such as `Food& Drinks (monthly)` or `Apple Cloud`. Parent/Section Row labels such as `Living expenses`, `Services` and `Insurance` group the tracker and are not valid targets.
- For a missing leaf, pick the allowed Parent/Section Row in `new_parent_category` and type the new label in `new_leaf_category`; leave `manual_category` empty on that row. The commit run registers it in `config/categories.yaml` (reported under `Category Registry Updates`) and may insert the row into the copied workbook when placement and parent formulas are safe.
- `learn_to_memory`: leave blank to learn the decision on commit; `no` for a one-off.
- Use `Category Options` to avoid derived, fixed, or formula-owned rows.
- Use `Audit` to spot-check every `auto` row with its `source`, `votes` and `reason`.

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

Prompt context is minimized: merchant identity, amount, date, direction, YAML leaf choices with descriptions, Guidance Aliases, and up to five nearest Category Memory neighbours. raw Nordea descriptions are excluded unless `include_raw_description: true` is deliberately configured. Nothing is sent to a hosted model.

Without a running local model the run still completes: provider failures, timeouts, and invalid or low-confidence answers are recorded in the report's `Local LLM Mode` section and audit log, and the affected rows become ordinary exceptions.

## 8. Per-Month Command (Older Months, PDF Fallback)

`monthly` always uses the newest CSV. For another month, or a PDF when no CSV export exists, run the per-month command. It does not ask the local models unless `--local-llm-suggestions` is given, and it is a dry run unless `--commit` is given:

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

Use `--statement-format nordea-pdf` for a PDF; expect more review because PDFs carry less merchant detail. `--config-dir` and `--output-dir` work as for `monthly`.

## 9. Proxy Split Transfer Rows

A Proxy Split Transfer is one bank transfer to an intermediary account used as evidence for several tracker allocations. Personal split rules belong in ignored `config/rules.local.yaml`.

For the Revolut family-transfer pattern, the configured fixed allocation is `8000 * 0.82 = 6560 DKK` for `Dad` and `4000 * 0.82 = 3280 DKK` for `Mom`; a matching Revolut expense must cover the full `9840 DKK` before it is split. Methods in the outputs:

- `proxy_split_source`: the original transfer, kept for audit and excluded from workbook totals.
- `proxy_split_allocation`: a counted fixed allocation such as `Dad` or `Mom`.
- `proxy_split_residual`: a Residual Review Line for the leftover of a larger transfer.
- `proxy_split_blocked`: a candidate kept review-only because it was underfunded or exceeded the rule's `monthly_limit`.

Residual decisions apply only to the current month and are not learned into Category Memory.

Review Required column order keeps transaction context first, then `manual_category`, `new_parent_category`, `new_leaf_category` and `learn_to_memory`, with split metadata (`split_role`, `split_rule`, `source_transaction_id`, `allocated_amount`, `residual_amount`) farther right.

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
