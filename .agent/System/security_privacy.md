# Security And Privacy

Last updated: 2026-09-26

## Public/Private Boundary

Public package artifacts are reusable code, synthetic or redacted fixtures, sample public configuration, docs, and durable agent-facing contracts. They must not contain real tracker values, real statement data, local profile paths, generated reports, Category Memory, Importer Profiles, private local rules, Guidance Aliases, proxy split rules, credentials, or logs.

Private profile artifacts are local-only and ignored by Git. They include real statements, tracker workbooks, copied workbooks, generated outputs, Category Memory, Importer Profiles, local rule overlays, Guidance Aliases, proxy split rules, credentials, and profile files.

The product direction is a Local Wealth-Tracker Agent, not an autonomous finance authority. Statement Import Assistant output and Importer Profile guesses remain review-only until confirmed by the user. Local model suggestions reach the workbook only through two-model Consensus under the Trust Policy (amount cap, never-auto list) and workbook safety checks; everything else is review-only.

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
- Hosted Judgment is opt-in only and not enabled: no hosted model is called by any command and no setting turns one on (`docs/adr/0005-hosted-judgment-deferred.md`).
- `outbound_redaction` (allowlist: redacted merchant, amount band, direction) stays in the package, tested but unused, for any future hosted adapter.
- The TypeSafe SDK is only the optional `hosted` extra; a default install does not include it.
- The parser and categorizer run locally.
- The original workbook is never modified directly.
- Commit mode creates a backup, then writes into the tracker in place; the Commit Ledger stays local.
- Reports and audit logs are traceable but local-only because they contain transaction descriptions.

## Local LLM Mode

- `wealth-tracker monthly` always asks the local models; the per-month command asks them only with explicit `--local-llm-suggestions`. Both call only the local Ollama HTTP API.
- Local LLM prompts should use minimized transaction context by default: the merchant text as it appears on the statement (the parsed merchant, else the description; case, digits and diacritics kept), amount, date, direction, allowed YAML leaf categories, prior low-confidence deterministic suggestion context when present, private reviewed policy guidance when available, private Guidance Aliases (merchant pattern and leaf category) when configured, and up to five local Category Memory neighbours (merchant identity and category) nearest to the row.
- The local prompt carries raw merchant text because normalisation garbles names (`7-ELEVEN 7060` loses its digits). For Nordea CSV rows the merchant text is the parsed description itself (`Name`, else `Title`). It goes only to the local Ollama API; it is not newly persisted, and Category Memory keys, memory-neighbour lookup, Guidance Alias matching and review decision validation still use the normalised merchant identity. Memory neighbours are shown by normalised identity.
- raw Nordea descriptions are excluded from Local LLM prompts by default, beyond the merchant text above (for Nordea CSV that is the whole `Name`/`Title` value), unless a future evaluation shows minimized context is insufficient and the operator explicitly enables that mode (`include_raw_description`); the description is then sent only when it differs from the merchant text.
- Hosted Judgment payloads stay behind `outbound_redaction`: the raw merchant text never leaves the machine.
- Local LLM output is review-only unless two distinct local models agree under the Trust Policy (ADR 0002). Consensus results enter Category Memory only on commit, with provenance `auto`, and categorise only after two consistent committed months (ADR 0004).
- Low-confidence Local LLM category responses should be ignored and reported rather than populating review suggestion fields.
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
