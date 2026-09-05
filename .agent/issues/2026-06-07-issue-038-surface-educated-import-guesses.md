---
type: issue
id: ISSUE-038
title: Surface Educated Import Guesses
status: done
slice_type: AFK
labels:
  - done
parent: 2026-06-07-prd-local-wealth-tracker-agent-public-package.md
blocked_by: []
created: 2026-06-07
---

# Surface Educated Import Guesses

## Parent

[PRD: Local Wealth-Tracker Agent Public Package](./2026-06-07-prd-local-wealth-tracker-agent-public-package.md)

## What To Build

Use local Importer Profiles to produce Educated Import Guesses for similar future imports. The guesses should make repeated formats easier to review by suggesting field mappings and transaction categories, while keeping high-confidence and low-confidence rows visible, filterable, and reviewable.

## Acceptance Criteria

- [x] Similar future imports can match an existing Importer Profile and produce Educated Import Guesses.
- [x] Guesses include confidence, reason, profile provenance, and whether the source format changed.
- [x] High-confidence guesses are visible and filterable so the user can set them aside during review.
- [x] Low-confidence guesses, changed layouts, unsupported currencies, invalid fields, duplicates, and out-of-period rows remain prominent review work.
- [x] Suggested transaction categories can be confirmed or corrected by the user before monthly planning uses them.
- [x] Tests cover profile matching, high-confidence filtering, low-confidence highlighting, changed-format fallback, and no silent trust.

## Blocked By

None - can start immediately.
