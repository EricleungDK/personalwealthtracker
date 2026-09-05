---
type: issue
id: ISSUE-039
title: Preserve Review-Only Financial Authority
status: done
slice_type: AFK
labels:
  - done
parent: 2026-06-07-prd-local-wealth-tracker-agent-public-package.md
blocked_by: []
created: 2026-06-07
---

# Preserve Review-Only Financial Authority

## Parent

[PRD: Local Wealth-Tracker Agent Public Package](./2026-06-07-prd-local-wealth-tracker-agent-public-package.md)

## What To Build

Connect the public package workflows back to the existing safety model: dry-run reports before writes, Category Memory learning only from explicit confirmed decisions and opt-in learning, model/importer suggestions as review-only assistance, workbook safety checks before planning writes, and commit mode writing only copied workbooks.

## Acceptance Criteria

- [x] Monthly planning rejects unreviewed unknown-format imports as trusted evidence.
- [x] Local model suggestions and Educated Import Guesses cannot directly write workbook values.
- [x] Category Memory learning still requires confirmed review decisions plus explicit learning opt-in.
- [x] Dry-run reports and audit logs trace parsed data, suggestions, review decisions, learned state, and planned workbook writes.
- [x] Commit mode continues to write only copied workbooks and preserves the original tracker.
- [x] Tests prove formulas, populated cells, derived rows, fixed rows, section totals, unsupported rows, unsupported columns, and ambiguous structures remain blocked.

## Blocked By

None - can start immediately.

## Implementation Notes

- Added `tests/test_financial_authority.py` to prove unreviewed unknown-format import artifacts remain untrusted and cannot be passed into monthly planning as trusted statement evidence.
- Restored the target-period validation compatibility helper and updated pipeline safety tests to patch the Trusted Statement Adapter layer.
- Verified Local LLM suggestions, Educated Import Guesses, Category Memory learning gates, dry-run/audit traces, copied-workbook commit behavior, and workbook safety blocks through the full suite.
- Verified with `PYTHONPATH=/tmp/pwt-deps:src python3 -m pytest` using project-declared runtime dependencies in `/tmp/pwt-deps`; 197 tests passed.
