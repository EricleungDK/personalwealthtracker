# Data Contracts

Last updated: 2026-05-21

## Transaction

Normalized statement row:

- `transaction_id`: deterministic hash from date, amount, description, and row order.
- `date`: booked date.
- `interest_date`: Nordea `Rentedato`, when available.
- `description`: categorization text from the statement parser. Nordea CSV prefers merchant-useful `Name` values and falls back to `Title`; Nordea PDF uses merged detail text.
- `amount`: booked DKK amount.
- `currency`: `DKK` for MVP 1.
- `direction`: `income` for non-negative amounts, `expense` for negative amounts.
- `balance`: statement balance after transaction, when available.
- `original_amount` and `original_currency`: optional metadata when a foreign card transaction line exposes the original amount.

Nordea CSV transactions may include raw source details such as `Name`, `Title`, `Sender`, `Recipient`, `Balance`, and `Reconciled` for audit. Account-number fields are retained only as source details and must not become categorization text or category-memory keys.

## CategorizedTransaction

- `transaction`: normalized transaction.
- `suggested_category`: existing tracker row category or null.
- `confidence`: deterministic confidence score.
- `categorization_method`: `category_memory`, `historical`, `recurring`, `rule`, `monthly_review_decision`, or `unmatched`.
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
- Review-required XLSX workbook.

Outputs are ignored because they may contain sensitive transaction data.

Report and audit outputs include the bank statement parser name, such as `nordea-csv` or `nordea-pdf`, so a run can be traced to the source format used.

Reports include a `Category Registry Updates` section. Existing `manual_category` decisions remain monthly review decisions, while validated `new_parent_category` and `new_leaf_category` rows are reported as category registry additions.

Audit logs use `category_registry_addition` records for validated new leaf registrations. These records include the parent category, leaf category, reporting period, source transaction IDs, statement parser, source statement, and target workbook.

## Review Workbook

The manual review workbook contains:

- `Review Required`: the operator work queue.
- `All Transactions`: audit context for every parsed transaction.
- `Category Options`: workbook/category registry option metadata.
- `Run Metadata`: reporting period, statement parser, generated timestamp, and transaction ID scheme.

Review decision columns:

- `manual_category`: current-month decision for an existing Leaf Category Row. It must target a leaf category from the YAML category registry.
- `new_parent_category`: allowed Parent/Section Row for a missing leaf category request.
- `new_leaf_category`: exact display label for the missing Leaf Category Row to add. It is mutually exclusive with `manual_category`.
- `learn_to_memory`: explicit opt-in flag. Only `yes`/truthy values allow future Category Memory learning.

The `Review Required` sheet should keep editable review decision columns close to the transaction description so the operator can classify rows without horizontal scanning. Less frequently edited workbook safety and audit columns can sit farther right. Preferred column order:

- `transaction_id`
- `date`
- `description`
- `amount`
- `manual_category`
- `new_parent_category`
- `new_leaf_category`
- `learn_to_memory`
- `split_role`
- `split_rule`
- `source_transaction_id`
- `allocated_amount`
- `residual_amount`
- `suggested_category`
- `method`
- `reason`
- `workbook_action`
- `target_cell`
- `workbook_reason`
- `merchant_identity`
- `confidence`
- `direction`

Older reviewed workbooks without `new_parent_category` and `new_leaf_category` remain importable for existing manual category decisions.

## Category Registry

`config/categories.yaml` is the durable category registry. It supports:

- parent entries with `allow_new_children` and `children`,
- leaf string entries,
- derived entries that are never direct transaction targets,
- explicit aliases that resolve old or short labels to registry labels.

Parent/Section Row labels group child rows and may allow reviewed new leaf requests. Leaf Category Row labels are the valid targets for `manual_category`, workbook value planning, and Category Memory learning. Derived rows such as workbook totals are allowed as context but not as write or memory targets.

The registry rejects duplicate labels using case-insensitive trimmed matching while preserving exact display labels in YAML and reports.

Category Memory learning validates against leaf categories. Learning skips Parent/Section Row labels, derived rows, missing categories, and other non-leaf targets. A newly registered leaf can be learned only after the reviewed second run has added it to the YAML registry.

## Future Proxy Split Rules

Proxy split rules should live in private local config when they contain personal intermediary names, family labels, or fixed amounts. A proxy split rule should define the transaction trigger, direction, conversion rate, fixed allocations, and whether residual review is required.

Configured allocation targets must be Leaf Category Row labels from the Category Registry. Allocation base amounts are converted to tracker currency with the configured proxy split conversion rate before contributing to monthly statement totals.

Proxy split allocation math should use decimal arithmetic. Each configured allocation is converted and rounded to 2 decimal places before residual calculation. Residual is calculated from the absolute source transaction amount minus the rounded allocation amounts. Residual amounts below 0.01 DKK are treated as zero; negative residual means the proxy split rule does not apply and the transaction remains review-only.

A proxy split transfer whose tracker-currency amount is smaller than the configured allocation total should remain review-only. A transfer that exactly covers the configured allocations should produce only the configured allocation lines. A larger transfer should produce configured allocation lines plus a residual review line tied to the original source transaction.

Residual review decisions apply to the current monthly run only and should not be imported into Category Memory, because the residual represents a leftover allocation rather than a stable merchant identity.

Recurring proxy split rules should support a monthly application limit. The Revolut family split rule should default to at most one automatic application per reporting month; if multiple Revolut expense candidates match, the run should require review instead of auto-splitting all candidates.

Categorized output should preserve the original source transaction as a proxy split source line for audit and should add separate proxy split allocation lines for the configured category allocations. The source line should not directly contribute to workbook totals; allocation lines contribute to their configured categories. If a residual amount exists, a residual review line should be emitted separately.

Proxy split allocation and residual lines should use deterministic IDs derived from the source transaction ID, split rule name, and split role. For example:

- `<source_transaction_id>:split:example_transfer:parent_a`
- `<source_transaction_id>:split:example_transfer:parent_b`
- `<source_transaction_id>:split:example_transfer:residual`

Review workbook rows for proxy split allocation and residual lines should expose split context metadata such as source transaction ID, split rule, split role, source amount, allocated amount, and residual amount. These metadata columns support auditability and should be placed so they do not push the primary review decision columns away from the transaction description.

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
