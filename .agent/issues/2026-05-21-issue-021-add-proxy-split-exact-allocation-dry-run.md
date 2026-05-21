---
type: issue
id: ISSUE-021
title: Add Proxy Split Exact Allocation Dry Run
status: done
slice_type: AFK
labels:
  - done
parent: 2026-05-21-prd-proxy-split-transfer-rules.md
blocked_by: []
created: 2026-05-21
---

# Add Proxy Split Exact Allocation Dry Run

## Parent

[PRD: Proxy Split Transfer Rules](./2026-05-21-prd-proxy-split-transfer-rules.md)

## What To Build

Add the first end-to-end proxy split path for an exact fixed-allocation Revolut family transfer. A private local proxy split rule should be loadable and validated, an exact matching Revolut expense should produce counted Dad and Mom allocation lines, and the original source transaction should remain visible for audit without contributing directly to workbook totals.

## Acceptance Criteria

- [x] Private local rules can define proxy split rules with a name, transaction trigger, direction, conversion rate, fixed allocations, and monthly application limit.
- [x] Proxy split allocation targets must be valid Leaf Category Row labels from the Category Registry.
- [x] Invalid proxy split categories, rates, base amounts, or missing allocation data fail config loading clearly.
- [x] An exact `9840 DKK` Revolut expense matching the family rule produces a Dad allocation of `6560.00 DKK` and a Mom allocation of `3280.00 DKK`.
- [x] The original Revolut transaction remains visible as a proxy split source line for audit.
- [x] The proxy split source line does not contribute directly to workbook totals.
- [x] Dad and Mom allocation lines contribute to workbook planning as deterministic category matches.
- [x] Split line IDs are deterministic and derived from source transaction ID, split rule name, and split role.
- [x] Dry-run report, categorized CSV, review CSV/XLSX, and audit output make the exact split traceable.
- [x] Tests cover config loading, validation, exact split output, workbook planning, report output, and audit output with synthetic data.

## Blocked By

None - can start immediately.
