---
type: issue
id: ISSUE-010
title: Add Mastercard And CSV Merchant Categorization
status: ready
slice_type: AFK
labels:
  - ready-for-agent
parent: 2026-05-13-prd-nordea-csv-bank-statement-ingestion.md
blocked_by:
  - ISSUE-008
created: 2026-05-13
---

# Add Mastercard And CSV Merchant Categorization

## Parent

[PRD: Nordea CSV Bank Statement Ingestion](./2026-05-13-prd-nordea-csv-bank-statement-ingestion.md)

## What To Build

Add configuration and categorization behavior that uses richer Nordea CSV merchant descriptions without changing workbook write safety. Mastercard rows must follow the user's workbook semantics: negative Mastercard payments are debt payments to `Nordea Credit Card`, while positive Mastercard rows are refund cashflow to a new `Mastercard refund` category.

## Acceptance Criteria

- [ ] `Mastercard refund` is added as a configured category.
- [ ] Negative `MASTERCARD` transactions map deterministically to `Nordea Credit Card`.
- [ ] Positive `MASTERCARD` transactions map deterministically to `Mastercard refund`.
- [ ] Mastercard rows are not categorized as ordinary spending categories.
- [ ] Merchant-rich CSV descriptions improve existing keyword/historical rules without loosening auto-write safety.
- [ ] Obvious CSV merchants such as `Google One` and `CBB MOBIL` are covered when they have existing workbook categories.
- [ ] Transport-like CSV merchants are handled only where the workbook category decision is clear.
- [ ] Tests cover positive/negative Mastercard behavior, merchant keyword matches from CSV descriptions, and review behavior for unknown merchants.

## Blocked By

- [ISSUE-008: Add Nordea CSV Transaction Parser](./2026-05-13-issue-008-add-nordea-csv-transaction-parser.md)
