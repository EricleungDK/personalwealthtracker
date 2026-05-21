---
type: issue
id: ISSUE-022
title: Emit And Apply Residual Split Review Lines
status: done
slice_type: AFK
labels:
  - done
parent: 2026-05-21-prd-proxy-split-transfer-rules.md
blocked_by:
  - ISSUE-021
created: 2026-05-21
---

# Emit And Apply Residual Split Review Lines

## Parent

[PRD: Proxy Split Transfer Rules](./2026-05-21-prd-proxy-split-transfer-rules.md)

## What To Build

Extend proxy split behavior for Revolut transfers that are larger than the fixed Dad/Mom allocation total. The run should emit Dad and Mom allocation lines plus a residual review line, then allow a reviewed monthly decision to categorize only that residual amount for the current run.

## Acceptance Criteria

- [x] A Revolut expense larger than `9840 DKK` produces Dad and Mom allocation lines plus one residual review line.
- [x] Residual amount is calculated from the absolute source amount minus the rounded fixed allocation amounts.
- [x] Residual amounts below `0.01 DKK` are treated as zero and do not produce a residual review line.
- [x] Residual review lines use deterministic source-derived split IDs.
- [x] Residual review lines are review-required until a Monthly Review Decision supplies a valid leaf category.
- [x] A reviewed residual decision applies only to the residual amount, not the whole source transaction.
- [x] Reviewed residual decisions preserve normal workbook safety checks.
- [x] Residual decisions are not imported into Category Memory even when `learn_to_memory=yes` is present.
- [x] Reports and audit output distinguish fixed allocation lines from residual review lines.
- [x] Tests cover larger transfers, zero residual dust, reviewed residual categorization, workbook planning, and Category Memory skip behavior.

## Blocked By

- [ISSUE-021: Add Proxy Split Exact Allocation Dry Run](./2026-05-21-issue-021-add-proxy-split-exact-allocation-dry-run.md)
