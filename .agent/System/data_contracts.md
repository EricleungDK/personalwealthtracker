# Data Contracts

Last updated: 2026-05-06

## Transaction

Normalized statement row:

- `transaction_id`: deterministic hash from date, amount, description, and row order.
- `date`: booked date.
- `interest_date`: Nordea `Rentedato`, when available.
- `description`: merged detail text.
- `amount`: booked DKK amount.
- `currency`: `DKK` for MVP 1.
- `direction`: `income` for non-negative amounts, `expense` for negative amounts.
- `balance`: statement balance after transaction, when available.
- `original_amount` and `original_currency`: optional metadata when a foreign card transaction line exposes the original amount.

## CategorizedTransaction

- `transaction`: normalized transaction.
- `suggested_category`: existing tracker row category or null.
- `confidence`: deterministic confidence score.
- `categorization_method`: `historical`, `rule`, or `unmatched`.
- `review_required`: true when the transaction must not be auto-written.
- `reason`: human-readable explanation for report and audit.

## TrackerUpdate

- `year` and `month`: target workbook period.
- `category`: tracker row name.
- `amount`: absolute monthly total for the category.
- `source_transactions`: transaction IDs included in the total.
- `target_row`, `target_column`, `target_cell`: resolved workbook target.
- `existing_value`: current workbook value before writing.
- `write_action`: `write`, `skip`, or `review`.
- `reason`: action explanation.

Direct value updates should target leaf workbook rows only. Derived workbook rows and section totals should appear in reports as skipped or formula-owned when encountered, not as writable targets.

Future period-column creation should be represented separately from value updates so reports can distinguish planned structure changes from financial cell writes. Dry-run output should expose the planned structure change before commit mode applies it.

Period-column creation records should include the target year/month and the source template period column used for formulas and formatting.

Year-block creation records should include the target year, the 12 period columns to create, and the source year block used as the template.

Structure-change records should distinguish preserved formulas, cleared copied manual values, and any deliberately retained pre-filled values. Retained pre-filled values should identify the configured carry-forward recurring row that allowed the value to remain.

Future writer config should distinguish `fixed_rows` from `carry_forward_rows`: fixed rows block automated overwrites, while carry-forward rows permit retaining copied recurring values during period/year creation.

## Outputs

Every run writes:

- Markdown monthly report.
- JSONL audit log.
- Categorized transaction CSV.
- Review-required CSV.

Outputs are ignored because they may contain sensitive transaction data.

## Future Investment Valuation

Investment statement ingestion should distinguish:

- `month_end_market_value`: the point-in-time value eligible for asset value rows.
- `market_value_currency`: the currency reported by the investment statement, expected to be USD initially.
- `fixed_conversion_rate`: the user-maintained USD-to-DKK rate used for tracker values.
- `applied_conversion_rate`: the exact rate recorded for the reporting month run.
- `tracker_currency_value`: the DKK value after applying the fixed conversion rate.
- `valuation_granularity`: whether the value is for a specific holding or a portfolio/account total.
- `holding_symbol` or `holding_name`: required when the value is holding-level.
- `units` or `shares`: audit metadata, not the value written to net worth rows.
- `contribution_amount`: cash movement eligible for cashflow rows, not asset valuation.

Investment valuation records should remain a separate evidence model from normalized bank transactions. They can be combined with bank transaction evidence during monthly workbook planning, but they should not be forced into the `Transaction` contract.

Cross-source mismatch records should link related evidence from different sources, describe the disagreement, and mark it for review without mutating either source record.

Applied conversion-rate metadata belongs in report and audit contracts, not in workbook update cells, unless a later workbook-structure decision introduces a dedicated place for it.

## Payroll Workbook Logic

Bank statement salary deposits may support net income rows, but they must not be used to infer payroll deduction rows. Payroll deduction rows such as taxes and labour market contribution should preserve existing workbook formulas or manual workbook logic unless a future source is explicitly introduced.

## Future Category Memory

Learned category memory should be stored separately from hand-written local rules, under ignored private generated data such as `data/category_memory/`.

Each learned mapping should be created only from a confirmed review decision and should preserve enough audit metadata to inspect or reset it later.

Matching keys should use a normalized merchant identity by default. Recurring learned mappings may include amount tolerance and day-window hints. Learned memory should avoid full raw descriptions when they contain changing references or sensitive account details.

A future reviewed decision import should be a separate input contract from raw review output. It should contain the transaction identifier or source fingerprint, the confirmed category, and enough metadata to derive the merchant identity and optional recurring match hints.
