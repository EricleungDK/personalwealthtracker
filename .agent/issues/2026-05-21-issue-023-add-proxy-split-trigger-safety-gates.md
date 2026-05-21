---
type: issue
id: ISSUE-023
title: Add Proxy Split Trigger Safety Gates
status: done
slice_type: AFK
labels:
  - done
parent: 2026-05-21-prd-proxy-split-transfer-rules.md
blocked_by:
  - ISSUE-021
created: 2026-05-21
---

# Add Proxy Split Trigger Safety Gates

## Parent

[PRD: Proxy Split Transfer Rules](./2026-05-21-prd-proxy-split-transfer-rules.md)

## What To Build

Add the fail-closed behavior for proxy split candidates that are unsafe to split automatically. Underfunded Revolut transfers and multiple matching Revolut candidates in the same Reporting Month should remain review-only instead of partially allocating or double-counting fixed family support.

## Acceptance Criteria

- [x] A matching Revolut expense below the fixed allocation total remains review-only.
- [x] A negative residual blocks the proxy split rule and reports the reason.
- [x] The family proxy split rule applies automatically at most once per Reporting Month.
- [x] Multiple Revolut expense candidates that could cover the fixed allocation total require review instead of splitting all candidates.
- [x] Multiple candidate reports show enough transaction context for the tracker owner to decide which transfer should be split.
- [x] No Dad or Mom allocation lines are emitted when the rule is blocked by underfunding or duplicate candidates.
- [x] Reports and audit output explain why a candidate stayed review-only.
- [x] Tests cover underfunded transfers, duplicate candidates, no double-counting, report output, and audit output.

## Blocked By

- [ISSUE-021: Add Proxy Split Exact Allocation Dry Run](./2026-05-21-issue-021-add-proxy-split-exact-allocation-dry-run.md)
