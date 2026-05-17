---
type: issue
id: ISSUE-012
title: Stabilize Transaction IDs For Review Decisions
status: done
slice_type: AFK
labels:
  - ready-for-agent
parent: 2026-05-16-prd-manual-review-workbook-and-category-feedback-loop.md
blocked_by: []
created: 2026-05-16
---

# Stabilize Transaction IDs For Review Decisions

## Parent

[PRD: Manual Review Workbook And Category Feedback Loop](./2026-05-16-prd-manual-review-workbook-and-category-feedback-loop.md)

## What To Build

Make parsed bank transaction IDs stable enough to support Monthly Review Decisions. IDs should be based on transaction content and deterministic duplicate disambiguation, not source row position or source file path. Expose the transaction ID scheme so future review artifacts can validate compatibility before applying reviewed decisions.

## Acceptance Criteria

- [x] Nordea CSV transaction IDs no longer depend on original parser row index.
- [x] Nordea PDF transaction IDs no longer depend on original parser row index.
- [x] Transaction IDs are stable when the same parsed transaction content appears in a different input order.
- [x] Duplicate-looking transactions remain distinguishable with a deterministic occurrence number.
- [x] Transaction IDs do not depend on source file path.
- [x] A readable transaction ID scheme version is available to reporting/review artifact code.
- [x] Existing strict currency and reporting-period validation behavior remains unchanged.
- [x] Tests cover repeated parses, changed ordering, duplicate transactions, CSV parsing, and PDF parsing.

## Blocked By

None - can start immediately.
