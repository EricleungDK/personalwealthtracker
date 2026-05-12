---
type: issue
id: ISSUE-007
title: Separate Workbook Cleanup Tasks
status: done
slice_type: AFK
labels:
  - ready-for-agent
parent: 2026-05-11-prd-monthly-tracker-workbook-updater-next-slices.md
blocked_by: []
created: 2026-05-11
---

# Separate Workbook Cleanup Tasks

## Parent

[PRD: Monthly Tracker Workbook Updater Next Slices](./2026-05-11-prd-monthly-tracker-workbook-updater-next-slices.md)

## What To Build

Keep one-off workbook cleanup tasks separate from monthly planning and commit mode. The tracker currency is DKK, and any visible workbook currency-label cleanup should be handled deliberately as a maintenance action rather than as a side effect of a monthly financial update.

This slice should establish the local workflow/command boundary for cleanup tasks without mixing them into the normal monthly updater path.

## Acceptance Criteria

- [x] Workbook cleanup tasks are clearly separate from monthly dry-run and commit mode.
- [x] Currency-label cleanup is treated as a one-off maintenance action.
- [x] Monthly update runs do not silently edit workbook labels or other non-monthly value content.
- [x] Cleanup output explains what workbook text/structure would change.
- [x] Cleanup behavior writes only to a copied workbook or requires an explicit maintenance-mode confirmation.
- [x] Tests cover that monthly runs do not perform cleanup side effects.

## Blocked By

None - can start immediately.
