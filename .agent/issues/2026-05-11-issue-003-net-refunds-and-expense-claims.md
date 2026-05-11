---
type: issue
id: ISSUE-003
title: Net Refunds And Expense Claims
status: blocked
slice_type: AFK
labels:
  - ready-for-agent
parent: 2026-05-11-prd-monthly-tracker-workbook-updater-next-slices.md
blocked_by:
  - ISSUE-001
created: 2026-05-11
---

# Net Refunds And Expense Claims

## Parent

[PRD: Monthly Tracker Workbook Updater Next Slices](./2026-05-11-prd-monthly-tracker-workbook-updater-next-slices.md)

## What To Build

Handle refunds and expense claims according to the monthly workbook updater model. Deterministic refunds should reduce the matched category total in the reporting month where they appear. Later-month refunds must not reopen or revise prior workbook periods. Identifiable reimbursement-like transactions should map to the existing `Expense claims` row only when deterministic; no separate offset model should be introduced.

## Acceptance Criteria

- [ ] Same-month deterministic refunds reduce the matched category total.
- [ ] Later-month deterministic refunds are recorded in the reporting month where they appear.
- [ ] Prior workbook periods are not reopened or modified for later-month refunds.
- [ ] Unmatched or vague refunds remain review-only.
- [ ] Deterministic reimbursement-like transactions can map to the existing `Expense claims` row.
- [ ] No separate reimbursement offset model is introduced.
- [ ] Reports show refund and claim reasoning clearly enough for review.
- [ ] Tests cover same-month refund netting, later-month refund behavior, unmatched refund review, and deterministic `Expense claims` mapping.

## Blocked By

- [ISSUE-001: Protect Workbook Row Authority](./2026-05-11-issue-001-protect-workbook-row-authority.md)
