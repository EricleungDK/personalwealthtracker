---
type: issue
id: ISSUE-008
title: Add Nordea CSV Transaction Parser
status: ready
slice_type: AFK
labels:
  - ready-for-agent
parent: 2026-05-13-prd-nordea-csv-bank-statement-ingestion.md
blocked_by: []
created: 2026-05-13
---

# Add Nordea CSV Transaction Parser

## Parent

[PRD: Nordea CSV Bank Statement Ingestion](./2026-05-13-prd-nordea-csv-bank-statement-ingestion.md)

## What To Build

Add a Nordea CSV bank statement parser that normalizes the known Nordea current-account CSV export into the existing transaction contract. The parser should produce merchant-rich descriptions for categorization while preserving raw CSV evidence in transaction details.

## Acceptance Criteria

- [ ] The parser accepts the Nordea CSV header shape with semicolon delimiter and UTF-8 BOM tolerance.
- [ ] CSV booking dates are parsed from `YYYY/MM/DD`.
- [ ] CSV amounts and balances are parsed from Danish decimal strings.
- [ ] Every row currency is validated against the expected statement currency.
- [ ] Missing or unexpected row currency fails with a row-specific error.
- [ ] Transaction description prefers useful `Name` and falls back to `Title`.
- [ ] Generic provider names such as `Vipps MobilePay` fall back to the more specific `Title`.
- [ ] `Sender` and `Recipient` account numbers are not used in `description` or `merchant`.
- [ ] Raw CSV fields are preserved in transaction details for audit/debugging.
- [ ] Synthetic or redacted CSV fixture tests cover food merchant, MobilePay title fallback, salary, Mastercard, unknown merchant, and currency validation.

## Blocked By

None - can start immediately.
