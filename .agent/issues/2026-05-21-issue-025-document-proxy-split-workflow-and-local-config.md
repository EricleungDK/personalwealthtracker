---
type: issue
id: ISSUE-025
title: Document Proxy Split Workflow And Local Config
status: done
slice_type: AFK
labels:
  - done
parent: 2026-05-21-prd-proxy-split-transfer-rules.md
blocked_by:
  - ISSUE-021
  - ISSUE-022
  - ISSUE-023
  - ISSUE-024
created: 2026-05-21
---

# Document Proxy Split Workflow And Local Config

## Parent

[PRD: Proxy Split Transfer Rules](./2026-05-21-prd-proxy-split-transfer-rules.md)

## What To Build

Update operator and system documentation so future runs and future agents understand proxy split transfers, the private local config shape, the Revolut family split behavior, residual review semantics, and the improved review workbook layout.

## Acceptance Criteria

- [x] Monthly workflow docs explain how proxy split transfers appear in dry-run outputs.
- [x] Monthly workflow docs explain that concrete personal split rules belong in ignored local config.
- [x] A safe example local config shows the proxy split rule shape without exposing real private data beyond the already approved documented Dad/Mom formula.
- [x] Docs explain exact, larger, smaller, and duplicate Revolut candidate behavior.
- [x] Docs explain that residual review decisions are current-month-only and not learned into Category Memory.
- [x] Project overview and system docs use the resolved Proxy Split Transfer terminology.
- [x] Review workbook docs explain the new preferred column order and split metadata fields.
- [x] Documentation tests cover the new workflow terms and expected user-facing guidance.

## Blocked By

- [ISSUE-021: Add Proxy Split Exact Allocation Dry Run](./2026-05-21-issue-021-add-proxy-split-exact-allocation-dry-run.md)
- [ISSUE-022: Emit And Apply Residual Split Review Lines](./2026-05-21-issue-022-emit-and-apply-residual-split-review-lines.md)
- [ISSUE-023: Add Proxy Split Trigger Safety Gates](./2026-05-21-issue-023-add-proxy-split-trigger-safety-gates.md)
- [ISSUE-024: Reorder Review Workbook And Add Split Metadata](./2026-05-21-issue-024-reorder-review-workbook-and-add-split-metadata.md)
