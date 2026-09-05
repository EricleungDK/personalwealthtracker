# Security And Privacy

Last updated: 2026-06-07

## Public/Private Boundary

Public package artifacts are reusable code, synthetic or redacted fixtures, sample public configuration, docs, and durable agent-facing contracts. They must not contain real tracker values, real statement data, local profile paths, generated reports, Category Memory, Importer Profiles, private local rules, proxy split rules, credentials, or logs.

Private profile artifacts are local-only and ignored by Git. They include real statements, tracker workbooks, copied workbooks, generated outputs, Category Memory, Importer Profiles, local rule overlays, proxy split rules, credentials, and profile files.

The product direction is a Local Wealth-Tracker Agent, not an autonomous finance authority. Local model output, Statement Import Assistant output, Importer Profile guesses, and category suggestions remain review-only until confirmed by the user and gated by workbook safety checks.

## Sensitive Files

The following are local-only and ignored:

- real bank statements, including local Nordea CSV exports and `bank-statement.pdf`,
- tracker workbooks and generated workbook copies,
- CSV/JSONL reports and audit logs,
- backups and processed files,
- Category Memory and Importer Profiles,
- private local rules, proxy split rules, and local profile files,
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
- Local LLM prompts should use minimized transaction context by default: merchant identity, amount, date, direction, allowed YAML leaf categories, prior low-confidence deterministic suggestion context when present, and private reviewed policy guidance when available.
- raw Nordea descriptions are excluded from Local LLM prompts by default unless a future evaluation shows minimized context is insufficient and the operator explicitly enables that mode.
- Local LLM output is review-only and must not auto-write workbook values or update Category Memory without a confirmed review decision.
- Low-confidence Local LLM category and new-leaf responses should be ignored and reported rather than populating review suggestion fields.
- Local LLM provider failures should fail closed to ordinary manual review rather than blocking the monthly run or silently broadening prompt data.
- `data/category_memory/reviewed_policy.local.md` is private generated/editable guidance and must stay out of Git with Category Memory.

## Review Safeguards

The writer skips or flags:

- formulas,
- populated manual cells,
- protected fixed rows,
- missing category rows,
- missing target month columns,
- unmatched transactions,
- low-confidence transactions.
