---
type: issue
id: ISSUE-034
title: Customize Supported Template Dimensions
status: done
slice_type: AFK
labels:
  - done
parent: 2026-06-07-prd-local-wealth-tracker-agent-public-package.md
blocked_by: []
created: 2026-06-07
---

# Customize Supported Template Dimensions

## Parent

[PRD: Local Wealth-Tracker Agent Public Package](./2026-06-07-prd-local-wealth-tracker-agent-public-package.md)

## What To Build

Support safe v1 template customization for known workbook dimensions only: categories, section labels, period columns, currency settings, and profile paths. Unsupported formula edits, arbitrary layout edits, ambiguous workbook structure, and unsupported template versions should be rejected or reported as review-required instead of applied.

## Acceptance Criteria

- [x] Users can customize categories and section labels within the supported template schema.
- [x] Users can configure Tracker Currency and have workbook/report assumptions reflect it.
- [x] Period-column creation works against the supported template schema and preserves formulas/formatting while clearing ordinary copied values.
- [x] Unsupported formula changes and arbitrary layout edits are rejected or reported as unsupported.
- [x] Validation messages explain unsupported workbook edits without implying the agent can repair arbitrary spreadsheets.
- [x] Tests cover allowed category, section, period, currency, and profile-path customization plus rejected unsupported edits.

## Blocked By

None - can start immediately.

## Implementation Notes

- Added `template-workbook customize` and `customize_template_workbook` for supported v1 label renames and Tracker Currency updates.
- Added template validation that rejects unsupported formula/layout edits, unknown labels, duplicate labels, blank labels, missing metadata, and unsupported template versions before saving customizations.
- Added setup profile path overrides for known private local paths.
- Added report currency assumption lines for Tracker Currency and Statement Currency.
- Verified with `PYTHONPATH=/tmp/pwt-deps:src python3 -m pytest tests/test_template_customization.py tests/test_setup_workspace.py tests/test_template_workbook.py tests/test_cli.py tests/test_workbook.py tests/test_reporting.py tests/test_documentation.py` using `openpyxl 3.1.5`.
