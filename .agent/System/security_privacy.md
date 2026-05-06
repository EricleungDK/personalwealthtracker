# Security And Privacy

Last updated: 2026-05-06

## Sensitive Files

The following are local-only and ignored:

- real bank statements, including `bank-statement.pdf`,
- tracker workbooks and generated workbook copies,
- CSV/JSONL reports and audit logs,
- backups and processed files,
- credentials, tokens, and environment files.

Only redacted fixtures should be committed for parser tests.

## Data Handling Defaults

- MVP 1 does not send financial data to external APIs or LLMs.
- The parser and categorizer run locally.
- The original workbook is never modified directly.
- Commit mode creates a backup and writes to a copied workbook.
- Reports and audit logs are traceable but local-only because they contain transaction descriptions.

## Review Safeguards

The writer skips or flags:

- formulas,
- populated manual cells,
- protected fixed rows,
- missing category rows,
- missing target month columns,
- unmatched transactions,
- low-confidence transactions.
