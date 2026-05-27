# Security And Privacy

Last updated: 2026-05-27

## Sensitive Files

The following are local-only and ignored:

- real bank statements, including local Nordea CSV exports and `bank-statement.pdf`,
- tracker workbooks and generated workbook copies,
- CSV/JSONL reports and audit logs,
- backups and processed files,
- credentials, tokens, and environment files.

Only redacted or synthetic fixtures should be committed for parser tests. Real CSV exports may be used for local smoke validation only while they remain in ignored paths.

## Data Handling Defaults

- MVP 1 does not send financial data to external APIs or LLMs.
- The parser and categorizer run locally.
- The original workbook is never modified directly.
- Commit mode creates a backup and writes to a copied workbook.
- Reports and audit logs are traceable but local-only because they contain transaction descriptions.

## Future Local LLM Mode

- Local LLM suggestions must be explicit opt-in, not automatic when a local provider is installed.
- Local LLM prompts should use minimized transaction context by default: merchant identity, amount, date, direction, and the allowed YAML leaf categories.
- Raw bank descriptions should not be sent to a local model unless a future evaluation shows minimized context is insufficient and the operator explicitly enables that mode.
- Local LLM output is review-only and must not auto-write workbook values or update Category Memory without a confirmed review decision.
- Local LLM provider failures should fail closed to ordinary manual review rather than blocking the monthly run or silently broadening prompt data.

## Review Safeguards

The writer skips or flags:

- formulas,
- populated manual cells,
- protected fixed rows,
- missing category rows,
- missing target month columns,
- unmatched transactions,
- low-confidence transactions.
