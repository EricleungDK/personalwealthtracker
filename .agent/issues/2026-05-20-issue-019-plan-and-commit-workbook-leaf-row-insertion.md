---
type: issue
id: ISSUE-019
title: Plan And Commit Workbook Leaf Row Insertion
status: ready
slice_type: AFK
labels:
  - ready-for-agent
parent: 2026-05-20-prd-yaml-category-registry-and-leaf-category-review-flow.md
blocked_by: []
created: 2026-05-20
---

# Plan And Commit Workbook Leaf Row Insertion

## Parent

[PRD: YAML Category Registry And Leaf Category Review Flow](./2026-05-20-prd-yaml-category-registry-and-leaf-category-review-flow.md)

## What To Build

When a registered leaf category does not exist in the tracker workbook, plan a workbook structure change and commit it only to a copied workbook when safe. The new row should be inserted under the selected parent row with consistent formatting and safe formula handling.

## Acceptance Criteria

- [ ] Workbook planning detects registered leaf categories missing from the tracker workbook.
- [ ] Dry-run output reports the planned leaf row insertion before commit.
- [ ] The planned insertion places the new leaf under the selected parent after existing sibling leaf rows and before the next parent/section boundary.
- [ ] Commit mode inserts the row only in a copied workbook.
- [ ] The original tracker workbook remains unchanged.
- [ ] New row formatting is copied from a nearby sibling leaf row when possible.
- [ ] Parent formulas are updated only when the existing formula range pattern is safely understood.
- [ ] Ambiguous section boundaries or formula patterns block the structure commit with a clear reason.
- [ ] Existing workbook value write safety remains unchanged.
- [ ] Tests cover missing-row planning, copied-workbook insertion, sibling formatting, safe formula update, blocked ambiguous formula update, and original-workbook preservation.

## Blocked By

None - can start immediately.
