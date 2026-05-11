---
type: issue
id: ISSUE-001
title: Protect Workbook Row Authority
status: ready
slice_type: AFK
labels:
  - ready-for-agent
parent: 2026-05-11-prd-monthly-tracker-workbook-updater-next-slices.md
blocked_by: []
created: 2026-05-11
---

# Protect Workbook Row Authority

## Parent

[PRD: Monthly Tracker Workbook Updater Next Slices](./2026-05-11-prd-monthly-tracker-workbook-updater-next-slices.md)

## What To Build

Teach the monthly tracker workbook updater which workbook rows are safe direct write targets and which rows are workbook-owned. The updater should write only source-backed leaf rows when all safety checks pass, preserve manual values, preserve formulas, and report formula-owned or section-total rows as skipped/reviewed rather than writable.

This slice should also handle salary-specific workbook authority: matched Nordea net salary deposits may target `Full-time job (net)`, but `Income (net)`, tax rows, labour contribution rows, and section totals remain derived workbook rows.

## Acceptance Criteria

- [ ] Workbook planning distinguishes leaf rows from derived workbook rows.
- [ ] `Income (net)` is never planned as a direct write target.
- [ ] Section totals such as `Cashflow`, `Assets`, `Investments`, `Living expenses`, `Services`, and `Total net worth` are never planned as direct write targets.
- [ ] Existing formula cells are skipped without modification.
- [ ] Existing manual values remain authoritative and produce review items rather than overwrites.
- [ ] A single deterministic Nordea net salary match can plan a write to `Full-time job (net)` when the target cell is safe.
- [ ] Multiple salary-like deposits in one reporting month are summed for reporting but require review before writing.
- [ ] Reports and review CSVs explain formula-owned, manual-value, derived-row, and salary multi-match decisions.
- [ ] Existing dry-run and commit-to-copy safety behavior remains intact.

## Blocked By

None - can start immediately.
