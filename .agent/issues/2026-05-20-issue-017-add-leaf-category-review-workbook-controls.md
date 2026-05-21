---
type: issue
id: ISSUE-017
title: Add Leaf Category Review Workbook Controls
status: ready
slice_type: AFK
labels:
  - ready-for-agent
parent: 2026-05-20-prd-yaml-category-registry-and-leaf-category-review-flow.md
blocked_by: []
created: 2026-05-20
---

# Add Leaf Category Review Workbook Controls

## Parent

[PRD: YAML Category Registry And Leaf Category Review Flow](./2026-05-20-prd-yaml-category-registry-and-leaf-category-review-flow.md)

## What To Build

Extend the manual review workbook so existing category decisions and missing-category requests are separate. `manual_category` should classify to existing leaf category rows, while `new_parent_category` and `new_leaf_category` should request a new leaf row under a valid parent.

## Acceptance Criteria

- [ ] `Review Required` includes optional `new_parent_category` and `new_leaf_category` columns.
- [ ] Existing reviewed workbooks without the new columns remain importable.
- [ ] `manual_category` dropdown values are existing leaf category rows.
- [ ] `new_parent_category` dropdown values are parent rows that allow new leaf children.
- [ ] Parent or section rows remain visible in category context with status metadata but are not valid `manual_category` targets.
- [ ] `Category Options` exposes parent/leaf metadata and whether new children are allowed.
- [ ] `new_leaf_category` preserves user-entered display text.
- [ ] Review workbook metadata remains compatible with the reviewed-decision import flow.
- [ ] Tests cover headers, dropdown ranges, category option metadata, old workbook compatibility, and parent/leaf separation.

## Blocked By

None - can start immediately.
