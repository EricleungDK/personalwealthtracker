---
type: issue
id: ISSUE-014
title: Apply Monthly Review Decisions
status: done
slice_type: AFK
labels:
  - ready-for-agent
parent: 2026-05-16-prd-manual-review-workbook-and-category-feedback-loop.md
blocked_by: []
created: 2026-05-16
---

# Apply Monthly Review Decisions

## Parent

[PRD: Manual Review Workbook And Category Feedback Loop](./2026-05-16-prd-manual-review-workbook-and-category-feedback-loop.md)

## What To Build

Allow a monthly run to explicitly consume a reviewed XLSX artifact and apply filled `manual_category` decisions by exact transaction ID. Manual decisions should override automatic categorization for those transactions while preserving all workbook write-safety rules.

## Acceptance Criteria

- [x] CLI supports an explicit `--review-decisions` option for monthly dry-run and commit planning.
- [x] The pipeline does not auto-detect review decision files from the reports directory.
- [x] Reviewed artifact reporting year and month must match the requested run.
- [x] Reviewed artifact transaction ID scheme must be supported.
- [x] Rows with blank `manual_category` are ignored as unreviewed.
- [x] Filled `manual_category` decisions apply only to matching transaction IDs in the current statement.
- [x] Missing or stale reviewed transaction IDs produce a clear warning or validation error and are not fuzzy-matched.
- [x] Monthly Review Decisions take precedence over automatic categorization for exact transaction IDs.
- [x] Applied manual decisions appear with categorization method `monthly_review_decision`.
- [x] Workbook write safety still blocks unsafe direct writes after manual decisions are applied.
- [x] Categorized CSV, audit output, review output, and report diagnostics reflect applied Monthly Review Decisions.
- [x] Tests cover explicit CLI usage, metadata validation, missing ID handling, precedence over automatic categorization, and unchanged workbook safety behavior.

## Blocked By

None - can start immediately.
