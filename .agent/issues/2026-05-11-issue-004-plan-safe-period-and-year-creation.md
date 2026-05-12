---
type: issue
id: ISSUE-004
title: Plan Safe Period And Year Creation
status: ready
slice_type: AFK
labels:
  - ready-for-agent
parent: 2026-05-11-prd-monthly-tracker-workbook-updater-next-slices.md
blocked_by:
  - ISSUE-001
created: 2026-05-11
---

# Plan Safe Period And Year Creation

## Parent

[PRD: Monthly Tracker Workbook Updater Next Slices](./2026-05-11-prd-monthly-tracker-workbook-updater-next-slices.md)

## What To Build

Add safe planned structure changes for missing workbook periods. Missing month/year creation must be visible in dry-run output before commit mode applies it to a copied workbook. Missing year creation should add a full 12-month year block when the existing workbook pattern is unambiguous.

New period columns should copy formulas, styles, widths, merged headers, and relevant structure from the immediately previous period/year block, while clearing ordinary copied manual values. Only explicitly configured carry-forward recurring rows may retain copied non-formula values. This carry-forward configuration must remain separate from fixed/protected rows.

## Acceptance Criteria

- [ ] Missing period columns are represented as planned structure changes, separate from value updates.
- [ ] Dry-run output reports planned period/year creation before commit mode applies it.
- [ ] Commit mode applies structure changes only to a copied workbook.
- [ ] Missing year creation creates a full 12-month year block when the prior pattern is unambiguous.
- [ ] Ambiguous workbook period patterns stop for review rather than guessing.
- [ ] New period columns copy formulas, styles, widths, merged headers, and relevant structure from the immediately previous period/year block.
- [ ] Ordinary copied manual values are cleared in newly created periods.
- [ ] Configured carry-forward recurring rows may retain copied non-formula values.
- [ ] `carry_forward_rows` is separate from fixed/protected rows.
- [ ] Tests cover month creation, year-block creation, dry-run reporting, ambiguous pattern review, formula preservation, cleared values, and carry-forward rows.

## Blocked By

- [ISSUE-001: Protect Workbook Row Authority](./2026-05-11-issue-001-protect-workbook-row-authority.md)
