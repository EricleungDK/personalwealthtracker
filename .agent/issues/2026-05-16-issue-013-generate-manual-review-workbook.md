---
type: issue
id: ISSUE-013
title: Generate Manual Review Workbook
status: done
slice_type: AFK
labels:
  - done
parent: 2026-05-16-prd-manual-review-workbook-and-category-feedback-loop.md
blocked_by: []
created: 2026-05-16
---

# Generate Manual Review Workbook

## Parent

[PRD: Manual Review Workbook And Category Feedback Loop](./2026-05-16-prd-manual-review-workbook-and-category-feedback-loop.md)

## What To Build

Add a human-friendly XLSX review artifact to monthly dry runs while keeping the existing CSV outputs. The workbook should be decision-ready: it should show full transaction context, expose manual category dropdowns sourced from the current Tracker Workbook fields, provide learnability/write-safety context, and include metadata needed for later imports.

## Acceptance Criteria

- [x] Dry-run output includes `review_required_<period>.xlsx` in addition to the existing review CSV.
- [x] The review workbook contains `Review Required`, `All Transactions`, `Category Options`, and `Run Metadata` sheets.
- [x] `Review Required` includes full transaction context: transaction ID, date, description, amount, direction, merchant identity, suggested category, confidence, method, and reason.
- [x] `Review Required` includes editable `manual_category` and `learn_to_memory` columns.
- [x] `All Transactions` includes every parsed transaction with categorization method, review flag, and reason.
- [x] `Category Options` is sourced from all non-empty row labels in the current Tracker Workbook category column.
- [x] `manual_category` dropdown values use exact Tracker Workbook row labels.
- [x] `learn_to_memory` is a dropdown with blank default plus `yes` and `no` choices.
- [x] Category options expose row number, learnability, and safety/status context for derived, fixed, or otherwise unsafe fields.
- [x] The workbook visibly flags unsafe selections or provides enough context for the user to avoid unsafe learning/writing decisions.
- [x] `Run Metadata` includes reporting year, reporting month, statement parser, generated timestamp, and transaction ID scheme.
- [x] Dry-run markdown report includes Categorization Quality diagnostics: classification rate, no-review rate, unmatched count, review-required count, and counts by categorization method.
- [x] Tests verify workbook sheets, headers, dropdowns, metadata, workbook-derived category options, and report diagnostics using synthetic data.

## Blocked By

None - can start immediately.
