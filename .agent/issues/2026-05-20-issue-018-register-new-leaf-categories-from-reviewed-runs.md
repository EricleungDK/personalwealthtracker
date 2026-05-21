---
type: issue
id: ISSUE-018
title: Register New Leaf Categories From Reviewed Runs
status: done
slice_type: AFK
labels:
  - done
parent: 2026-05-20-prd-yaml-category-registry-and-leaf-category-review-flow.md
blocked_by: []
created: 2026-05-20
---

# Register New Leaf Categories From Reviewed Runs

## Parent

[PRD: YAML Category Registry And Leaf Category Review Flow](./2026-05-20-prd-yaml-category-registry-and-leaf-category-review-flow.md)

## What To Build

Allow a reviewed second run to validate new leaf category requests from the review workbook, update the YAML category registry, and classify the current transaction to the newly registered leaf category. This registration is a category-registry update, not a workbook financial value write.

## Acceptance Criteria

- [x] Reviewed decision import reads optional `new_parent_category` and `new_leaf_category` columns.
- [x] A row cannot fill both `manual_category` and `new_leaf_category`.
- [x] A `new_leaf_category` row must include a valid `new_parent_category`.
- [x] `new_parent_category` must be a registry parent that allows new leaf children.
- [x] New leaf labels are rejected when they duplicate an existing category after trim/case normalization.
- [x] Valid new leaf labels are written to the YAML category registry with deterministic formatting.
- [x] The reviewed second run reports registered category additions.
- [x] The reviewed second run classifies the transaction to the newly registered leaf category.
- [x] Workbook financial values are not written unless normal workbook commit mode is requested.
- [x] Existing `manual_category` decisions continue to work.
- [x] Tests cover valid registration, invalid parent, duplicate leaf, mutually exclusive columns, report output, and current-month classification to the new leaf.

## Blocked By

None - can start immediately.
