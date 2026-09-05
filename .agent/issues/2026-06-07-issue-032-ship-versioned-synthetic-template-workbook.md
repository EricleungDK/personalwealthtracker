---
type: issue
id: ISSUE-032
title: Ship Versioned Synthetic Template Workbook
status: done
slice_type: AFK
labels:
  - done
parent: 2026-06-07-prd-local-wealth-tracker-agent-public-package.md
blocked_by: []
created: 2026-06-07
---

# Ship Versioned Synthetic Template Workbook

## Parent

[PRD: Local Wealth-Tracker Agent Public Package](./2026-06-07-prd-local-wealth-tracker-agent-public-package.md)

## What To Build

Add a clean synthetic Template Excel Workbook that can ship with the public package. The template should be inspired by the supported tracker schema, include template version metadata, and contain no real values, private categories, personal sheet names, hidden assumptions, or financial history.

## Acceptance Criteria

- [x] The package contains or can generate a synthetic Template Excel Workbook with no private data.
- [x] The template includes explicit version metadata that workbook adapters can validate.
- [x] Template categories, section labels, formulas, period structure, and currency defaults are generic and documented.
- [x] Workbook validation accepts the shipped template version and rejects missing or unsupported template metadata.
- [x] Synthetic workbook fixtures cover the public template without relying on the owner's private workbook.
- [x] Tests prove the template can be loaded, inspected, and used by existing workbook safety checks.

## Blocked By

None - can start immediately.

## Implementation Notes

- Added `src/personal_wealth_tracker/template_workbook.py` with a generated synthetic workbook, hidden template metadata, generic v1 rows, and metadata validation.
- Added `tests/test_template_workbook.py` coverage for template generation, metadata validation, unsupported metadata rejection, existing workbook safety checks, and the `template-workbook create` CLI path.
- Added `docs/template_workbook.md` and README setup notes for the public template command.
- Verified with `PYTHONPATH=src python3 -m pytest tests/test_template_workbook.py`, which ran the dependency-backed workbook generation, metadata validation, and workbook safety checks with `openpyxl`.
