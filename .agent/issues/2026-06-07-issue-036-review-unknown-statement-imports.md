---
type: issue
id: ISSUE-036
title: Review Unknown Statement Imports
status: done
slice_type: AFK
labels:
  - done
parent: 2026-06-07-prd-local-wealth-tracker-agent-public-package.md
blocked_by: []
created: 2026-06-07
---

# Review Unknown Statement Imports

## Parent

[PRD: Local Wealth-Tracker Agent Public Package](./2026-06-07-prd-local-wealth-tracker-agent-public-package.md)

## What To Build

Add the first Statement Import Assistant path for unknown statement formats. The assistant may use mocked local model output in tests, but every extracted row must become an Untrusted Imported Transaction that requires user review before monthly planning can treat it as confirmed evidence.

## Acceptance Criteria

- [x] Unknown-format import produces a review artifact instead of trusted monthly planning input.
- [x] Review artifacts expose date, amount, currency, description, direction, source row, provenance, confidence, and validation warnings.
- [x] Missing dates, invalid amounts, unsupported currencies, duplicate rows, changed layouts, and out-of-period transactions are visible in diagnostics.
- [x] Local model assistance is optional and unavailable-model failures do not block deterministic workflows.
- [x] No unknown-format model output can directly create workbook write permission.
- [x] Tests use mocked local model output and synthetic unknown-format inputs only.

## Blocked By

None - can start immediately.
