---
type: issue
id: ISSUE-006
title: Combine Monthly Planning Evidence
status: blocked
slice_type: AFK
labels:
  - ready-for-agent
parent: 2026-05-11-prd-monthly-tracker-workbook-updater-next-slices.md
blocked_by:
  - ISSUE-001
  - ISSUE-005
created: 2026-05-11
---

# Combine Monthly Planning Evidence

## Parent

[PRD: Monthly Tracker Workbook Updater Next Slices](./2026-05-11-prd-monthly-tracker-workbook-updater-next-slices.md)

## What To Build

Combine multiple evidence types into one monthly planning run for a reporting month. Nordea bank statements remain the source for cashflow evidence. Investment statements remain the source for asset value evidence. The workbook planner should combine available evidence into one proposed update set and one report, while keeping source authority separate.

Cross-source mismatches should be reported for review and must not let one source override another outside its evidence type.

## Acceptance Criteria

- [ ] A monthly planning run can accept Nordea cashflow evidence and investment valuation evidence for the same reporting month.
- [ ] Bank transaction evidence and investment valuation evidence remain separate models until workbook planning/reporting.
- [ ] The report presents one proposed workbook update set for the reporting month.
- [ ] Cross-source mismatches are reported for review.
- [ ] A cross-source mismatch does not mutate either source record.
- [ ] One source cannot override another outside its evidence type.
- [ ] Tests cover combined planning, combined report output, and mismatch records.

## Blocked By

- [ISSUE-001: Protect Workbook Row Authority](./2026-05-11-issue-001-protect-workbook-row-authority.md)
- [ISSUE-005: Add Investment Statement Evidence](./2026-05-11-issue-005-add-investment-statement-evidence.md)
