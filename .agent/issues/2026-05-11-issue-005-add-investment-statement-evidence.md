---
type: issue
id: ISSUE-005
title: Add Investment Statement Evidence
status: ready
slice_type: HITL
labels:
  - ready-for-agent
parent: 2026-05-11-prd-monthly-tracker-workbook-updater-next-slices.md
blocked_by: []
created: 2026-05-11
---

# Add Investment Statement Evidence

## Parent

[PRD: Monthly Tracker Workbook Updater Next Slices](./2026-05-11-prd-monthly-tracker-workbook-updater-next-slices.md)

## What To Build

Define and implement investment statement evidence as a separate source model from Nordea bank transactions. This issue is HITL because implementation depends on the actual investment statement format. The source should prove month-end market values or holdings, not cashflow from bank transfers.

Investment values are expected in USD and should be converted to DKK using a user-maintained fixed conversion rate. The applied conversion rate must appear in reports and audit logs, not workbook cells. Explicit holding-level values may map to individual asset rows; total-only values may map only to configured total rows or review. Crypto and digital assets remain out of scope until a dedicated valuation source exists.

## Acceptance Criteria

- [ ] The investment statement contract is separate from normalized bank transactions.
- [ ] The contract represents month-end market value, source currency, applied conversion rate, tracker-currency value, valuation granularity, and holding identity when present.
- [ ] USD values convert to DKK using a user-maintained fixed conversion rate.
- [ ] The applied conversion rate is recorded in reports and audit logs.
- [ ] Conversion-rate metadata is not written into workbook cells.
- [ ] Explicit holding-level values can map to individual asset value rows.
- [ ] Total-only portfolio values require a configured total row or remain review-only.
- [ ] Bank transfers to investing are not used as proof of asset values.
- [ ] Crypto and digital asset rows remain out of scope.
- [ ] Tests cover conversion, audit/report rate output, holding-level mapping, total-only review, and no crypto automation.

## Blocked By

None - can start after the user provides or describes the investment statement format.
