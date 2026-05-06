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

## Outputs

Every run writes:

- Markdown monthly report.
- JSONL audit log.
- Categorized transaction CSV.
- Review-required CSV.

Outputs are ignored because they may contain sensitive transaction data.
