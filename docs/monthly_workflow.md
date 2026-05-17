# Monthly Tracker Workflow

Use this runbook when updating the tracker workbook for one reporting month.

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
- Use `manual_category` to record the current-month category decision.
- Leave `learn_to_memory` blank unless a merchant decision should be considered for future Category Memory learning.
- Use the `Category Options` sheet to avoid derived, fixed, formula-owned, or otherwise unsafe category choices.
- Use the `All Transactions` sheet to debug low classification or no-review rates.

The `review_required_<year>_<month>.csv` file remains available for simple inspection and automation:

- Unmatched transactions need manual category decisions.
- Populated workbook cells remain review-only.
- Formula-owned or fixed rows should not be overwritten.
- Positive Mastercard rows should map to `Mastercard refund`.
- Negative Mastercard rows should map to `Nordea Credit Card`.

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
- Manual categories must still match exact row labels in the current tracker workbook.
- Reviewed transactions use the `monthly_review_decision` categorization method.
- The reviewed workbook must match the run's reporting period and transaction ID scheme.
- Stale or unknown transaction IDs fail the run instead of being guessed.

If a review workbook fails because the transaction ID scheme changed after a code update, regenerate the review workbook from a fresh dry run before applying decisions.

This dry run still does not modify the workbook. Check the updated report and categorized transactions before learning memory or committing.
If `--review-decisions` points at the default generated review workbook, the reviewed input is preserved and the follow-up review workbook is written as `review_required_<year>_<month>_after_decisions.xlsx`.

## 5. Optionally Learn Future Memory

After editing the review workbook, import only rows where `manual_category` is filled and `learn_to_memory` is `yes` into category memory:

```bash
uv run wealth-tracker learn-category-memory \
  --decisions "reports/review_required_2026_apr.xlsx"
```

The command still accepts reviewed CSV files for automation and older workflows.
Learning and workbook commit are separate steps. `manual_category` fixes the current month; `learn_to_memory` is an explicit opt-in for future runs. Rows with blank or non-yes `learn_to_memory` are not learned, and non-learnable category options are skipped.
Reviewed XLSX learning validates the workbook metadata and supported transaction ID scheme. Learned Category Memory is used before hand-written historical mappings, recurring rules, and keyword rules in future monthly runs.

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
