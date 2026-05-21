---
type: issue
id: ISSUE-009
title: Route Bank Statement Format And Report Parser
status: done
slice_type: AFK
labels:
  - done
parent: 2026-05-13-prd-nordea-csv-bank-statement-ingestion.md
blocked_by:
  - ISSUE-008
created: 2026-05-13
---

# Route Bank Statement Format And Report Parser

## Parent

[PRD: Nordea CSV Bank Statement Ingestion](./2026-05-13-prd-nordea-csv-bank-statement-ingestion.md)

## What To Build

Route monthly bank statement ingestion through either Nordea CSV or Nordea PDF parsing. Keep automatic routing as the default, add explicit format selection, and expose the parser used in report and audit outputs.

## Acceptance Criteria

- [x] CLI supports `--statement-format auto|nordea-csv|nordea-pdf`.
- [x] `auto` routes `.csv` to the Nordea CSV parser and `.pdf` to the Nordea PDF parser.
- [x] Explicit `nordea-csv` and `nordea-pdf` modes override extension inference.
- [x] Unsupported extensions in `auto` mode fail with an actionable error.
- [x] The pipeline preserves strict target reporting-month validation for parsed transactions.
- [x] Markdown report includes the bank statement parser used.
- [x] Audit JSONL includes the bank statement parser used.
- [x] Existing PDF tests and behavior remain supported.
- [x] Pipeline and CLI tests cover CSV routing, PDF routing, explicit routing, and unsupported format errors.

## Blocked By

- [ISSUE-008: Add Nordea CSV Transaction Parser](./2026-05-13-issue-008-add-nordea-csv-transaction-parser.md)
