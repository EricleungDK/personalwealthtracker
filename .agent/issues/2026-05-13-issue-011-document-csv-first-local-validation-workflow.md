---
type: issue
id: ISSUE-011
title: Document CSV First Local Validation Workflow
status: done
slice_type: AFK
labels:
  - done
parent: 2026-05-13-prd-nordea-csv-bank-statement-ingestion.md
blocked_by:
  - ISSUE-009
  - ISSUE-010
created: 2026-05-13
---

# Document CSV First Local Validation Workflow

## Parent

[PRD: Nordea CSV Bank Statement Ingestion](./2026-05-13-prd-nordea-csv-bank-statement-ingestion.md)

## What To Build

Document and validate the CSV-first monthly workflow without committing real financial data. The user may run local smoke validation against ignored real CSV files, while committed tests must use synthetic or redacted fixtures.

## Acceptance Criteria

- [x] User-facing docs explain that Nordea CSV is preferred for bank cashflow categorization.
- [x] Docs explain PDF remains supported as fallback/legacy input.
- [x] Docs show example dry-run commands for `--statement-format auto` and explicit CSV mode.
- [x] Docs state real CSV files remain ignored and must not be committed.
- [x] Docs describe local smoke validation against a real ignored CSV.
- [x] Docs explain that investment statements remain separate future PDF evidence.
- [x] Tests or checks confirm committed fixtures are synthetic/redacted and real CSV paths are not required.

## Blocked By

- [ISSUE-009: Route Bank Statement Format And Report Parser](./2026-05-13-issue-009-route-bank-statement-format-and-report-parser.md)
- [ISSUE-010: Add Mastercard And CSV Merchant Categorization](./2026-05-13-issue-010-add-mastercard-and-csv-merchant-categorization.md)
