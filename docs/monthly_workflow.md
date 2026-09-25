# Monthly Tracker Workflow

Use this runbook when updating the tracker workbook for one reporting month.

For a non-technical map of the project structure, components, outputs, scripts, and terminology, see [project_overview.md](project_overview.md).

## 1. Prepare Local Inputs

- Export the Nordea current-account CSV for the reporting month.
- Keep the real CSV in an ignored location, such as `data/raw_statements/`.
- Keep the tracker workbook local, for example `Net Worth Tracker.xlsx`.
- Do not move real CSV/PDF/XLSX files into `tests/fixtures/` or any committed path.

Nordea CSV is the preferred bank cashflow source because it includes merchant names. Nordea PDF is still available as a fallback when a CSV export is not available.

## 2. Run A CSV Dry Run

```bash
uv run wealth-tracker \
  --tracker "Net Worth Tracker.xlsx" \
  --statement "data/raw_statements/ignored-nordea-export.csv" \
  --statement-format auto \
  --year 2026 \
  --month Apr
```

Use `--statement-format nordea-csv` if you want to force CSV parsing.

Dry-run does not modify the workbook. It writes local outputs under `reports/`:

- `report_<year>_<month>.md` - human-readable run summary and planned workbook changes.
- `categorized_transactions_<year>_<month>.csv` - categorization result for every transaction.
- `review_required_<year>_<month>.csv` - transactions and workbook updates that need review.
- `review_required_<year>_<month>.xlsx` - manual review workbook with transaction context, category dropdowns from the tracker workbook, category option safety context, and run metadata.
- `audit_<year>_<month>.jsonl` - machine-readable audit records.

### Optional Local LLM Mode

Local LLM Mode is explicit opt-in. It never runs merely because Ollama is installed. Add `--local-llm-suggestions` only when you want review-only local model assistance:

```bash
uv run wealth-tracker \
  --tracker "Net Worth Tracker.xlsx" \
  --statement "data/raw_statements/ignored-nordea-export.csv" \
  --statement-format auto \
  --year 2026 \
  --month Apr \
  --local-llm-suggestions
```

The committed defaults target `gemma4:12b` through Ollama's local HTTP API, with `gemma4:e4b` as the fallback model and a 180-second cold-start provider timeout; `keep_alive` keeps the model warm between rows. Settings live under `local_llm` in `config/settings.yaml`.

Local model output stays in review: the Trust Policy requires two agreeing model votes (`trust_policy.min_agreement`) and a single local model casts one. Existing high-confidence deterministic matches, Monthly Review Decisions, Category Memory matches, and proxy split allocations keep `auto` authority, except that any automatic row above `trust_policy.auto_max_amount` (default 1000 DKK) or in `trust_policy.never_auto_categories` goes to review. Local LLM suggestions reuse the existing `suggested_category`, `method`, `confidence`, and `reason` fields in the review workbook; no primary LLM columns are added.

Prompt context is minimized by default: merchant identity, amount, date, direction, YAML leaf category choices with their descriptions, up to five nearest Category Memory neighbours, and any existing low-confidence rule/recurring suggestion context. raw Nordea descriptions are excluded unless `include_raw_description: true` is deliberately configured later for evaluation.

If Ollama is unavailable, the model is missing, a call times out, a response is invalid, or a category response is below the review threshold, the run continues with ordinary manual review output. The report's `Local LLM Mode` section and audit log show eligible rows, provider attempts, existing-leaf suggestions, NONE answers, low-confidence responses ignored, invalid responses, provider failures, and warnings.

## 3. Review The Outputs

Check the report first:

- Confirm `Statement parser: nordea-csv`.
- Confirm the reporting month is correct.
- Check the `Categorization Quality` section for classification rate, no-review rate, unmatched count, review-required count, and method counts.
- Review planned structure changes before commit mode.
- Review proposed workbook writes and skipped/review-only updates.

Then check `review_required_<year>_<month>.xlsx` for manual classification:

- Use the `Review Required` sheet as the work queue.
- Review rows can be transaction-level review items or categorized transactions whose workbook update is blocked; use `workbook_action`, `target_cell`, and `workbook_reason` to understand the block.
- Treat workbook grouping rows such as `Living expenses`, `Services`, and `Insurance` as Parent/Section Row labels. They organize the tracker and are not valid transaction category targets.
- Treat rows under those sections, such as `Food& Drinks (monthly)` or `Apple Cloud`, as Leaf Category Row labels. These are the valid existing targets for current-month decisions, workbook updates, and Category Memory learning.
- Use `manual_category` to record the current-month category decision when the correct Leaf Category Row already exists.
- Use `new_parent_category` and `new_leaf_category` when the correct leaf category is missing. Select the allowed Parent/Section Row in `new_parent_category`, then type the exact new display label in `new_leaf_category`.
- Do not fill both `manual_category` and `new_leaf_category` on the same review row.
- Leave `learn_to_memory` blank unless a merchant decision should be considered for future Category Memory learning.
- Use the `Category Options` sheet to distinguish parent, derived, and leaf rows and to avoid derived, fixed, formula-owned, or otherwise unsafe category choices.
- Use the `All Transactions` sheet to debug low classification or no-review rates.

The `review_required_<year>_<month>.csv` file remains available for simple inspection and automation:

- Unmatched transactions need manual category decisions.
- Populated workbook cells remain review-only.
- Formula-owned or fixed rows should not be overwritten.
- Positive Mastercard rows should map to `Mastercard refund`.
- Negative Mastercard rows should map to `Nordea Credit Card`.

### Proxy Split Transfer Rows

A Proxy Split Transfer is a single bank-statement transfer to an intermediary account or service that is used as source evidence for multiple tracker allocations. Concrete personal split rules belong in ignored `config/rules.local.yaml`, not in tracked public config.

For the Revolut family-transfer pattern, the configured fixed allocation is `8000 * 0.82 = 6560 DKK` for `Parent A` and `4000 * 0.82 = 3280 DKK` for `Parent B`. A matching Revolut expense must cover the full `9840 DKK` allocation total before the rule can split it.

Dry-run outputs use these categorization methods:

- `proxy_split_source`: the original transfer kept for audit and excluded from direct workbook totals.
- `proxy_split_allocation`: a counted fixed allocation such as `Parent A` or `Parent B`.
- `proxy_split_residual`: a Residual Review Line for the leftover amount from a larger transfer.
- `proxy_split_blocked`: a candidate that stayed review-only because it was underfunded or the number of same-month candidates exceeded the rule's configured `monthly_limit`.

Exact `9840 DKK` transfers produce only Parent A and Parent B allocation lines. Larger transfers produce Parent A and Parent B allocations plus a residual row for current-month review. Smaller transfers and candidates over the configured monthly limit stay review-only. Set `monthly_limit` in `config/rules.local.yaml` to the number of same-month transfers that are expected to receive the fixed Parent A/Parent B split. Residual review decisions apply only to the current month and should not be learned into Category Memory.

Review Required column order keeps the core transaction context first, then `manual_category`, `new_parent_category`, `new_leaf_category`, and `learn_to_memory`, with split metadata such as `split_role`, `split_rule`, `source_transaction_id`, `allocated_amount`, and `residual_amount` farther right.

## 4. Apply Monthly Review Decisions

After editing `review_required_<year>_<month>.xlsx`, run another dry run with the reviewed workbook:

```bash
uv run wealth-tracker \
  --tracker "Net Worth Tracker.xlsx" \
  --statement "data/raw_statements/ignored-nordea-export.csv" \
  --statement-format auto \
  --year 2026 \
  --month Apr \
  --review-decisions "reports/review_required_2026_apr.xlsx"
```

Review decisions are current-month overrides:

- Filled `manual_category` values are applied by exact `transaction_id`.
- Blank `manual_category` values are ignored.
- Manual categories must be existing tracker workbook labels or Leaf Category Row labels from the YAML category registry.
- Filled `new_parent_category` and `new_leaf_category` values request a missing Leaf Category Row under an allowed Parent/Section Row.
- New leaf category requests are validated against `config/categories.yaml`, reject duplicate labels, and are reported in the `Category Registry Updates` report section.
- A reviewed second run can register the new leaf category in YAML during dry-run behavior. This is a category-registry update, not a workbook financial value write.
- Reviewed transactions use the `monthly_review_decision` categorization method.
- The reviewed workbook must match the run's reporting period and transaction ID scheme.
- Stale or unknown transaction IDs fail the run instead of being guessed.

If a review workbook fails because the transaction ID scheme changed after a code update, regenerate the review workbook from a fresh dry run before applying decisions.

This dry run still does not modify the workbook. Check the updated report and categorized transactions before learning memory or committing.
If a newly registered Leaf Category Row is not present in the tracker workbook yet, the report shows a planned structure change. Commit mode may insert that row into a copied workbook only when placement, sibling formatting, and parent formulas are safe to update.
If `--review-decisions` points at the default generated review workbook, the reviewed input is preserved and the follow-up review workbook is written as `review_required_<year>_<month>_after_decisions.xlsx`.

## 5. Optionally Learn Future Memory

After editing the review workbook, import only rows where either `manual_category` or a reviewed `new_leaf_category` is filled and `learn_to_memory` is `yes` into category memory:

```bash
uv run wealth-tracker learn-category-memory \
  --decisions "reports/review_required_2026_apr.xlsx" \
  --config-dir config
```

The command still accepts reviewed CSV files for automation and older workflows.
Learning and workbook commit are separate steps. `manual_category` and reviewed `new_leaf_category` choices fix the current month; `learn_to_memory` is an explicit opt-in for future runs. Rows with blank or non-yes `learn_to_memory` are not learned, and non-learnable category options are skipped.
Reviewed XLSX learning validates the workbook metadata, supported transaction ID scheme, and YAML leaf category registry. Category Memory skips Parent/Section Row labels, derived rows, missing categories, fixed rows, and other non-leaf targets. A newly registered Leaf Category Row can be learned after the reviewed second run has added it to `config/categories.yaml`, even before the new row has been inserted into the tracker workbook.
Learned Category Memory is used before hand-written historical mappings, recurring rules, and keyword rules in future monthly runs.

The same learning step updates `data/category_memory/reviewed_policy.local.md`. The auto-generated section lists learned merchant/category examples, and the `## Manual Guidance` section is preserved for your edits. Local LLM Mode may include this policy as review guidance, but it is not model training, not workbook-write authority, and not Category Memory by itself.

After learning, run the dry-run again with `--review-decisions` and review the new categorization before committing workbook changes.

## 6. Commit To A Copied Workbook

Only commit after the dry-run output looks correct:

```bash
uv run wealth-tracker \
  --tracker "Net Worth Tracker.xlsx" \
  --statement "data/raw_statements/ignored-nordea-export.csv" \
  --statement-format auto \
  --year 2026 \
  --month Apr \
  --review-decisions "reports/review_required_2026_apr.xlsx" \
  --commit
```

Commit mode:

- creates a backup under `data/backups/`,
- writes only to a copied workbook under `data/processed/`,
- preserves the original workbook,
- skips unsafe workbook updates.

If there were no current-month manual decisions, omit `--review-decisions`.

## 7. Optional PDF Fallback

Use PDF fallback only when the CSV export is unavailable:

```bash
uv run wealth-tracker \
  --tracker "Net Worth Tracker.xlsx" \
  --statement "bank-statement.pdf" \
  --statement-format nordea-pdf \
  --year 2026 \
  --month Apr
```

PDF output may contain less merchant detail than CSV, so expect more manual review.

## 8. Separate Maintenance Tasks

Workbook cleanup tasks are not part of the monthly run. For currency-label cleanup, use the separate command:

```bash
uv run wealth-tracker cleanup-currency-labels \
  --tracker "Net Worth Tracker.xlsx" \
  --output-dir reports
```

Use `--commit` only when you want the cleanup written to a copied workbook.

## 9. Privacy Rules

- Do not commit real bank statements, CSV exports, tracker workbooks, generated reports, backups, logs, or category memory.
- Use real CSV exports only for local smoke validation.
- Committed CSV fixtures must be synthetic or redacted.
- Investment statements remain separate future PDF evidence and are not part of this bank cashflow workflow.
