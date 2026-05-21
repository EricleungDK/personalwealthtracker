---
type: issue
id: ISSUE-020
title: Gate Category Memory And Document Leaf Category Lifecycle
status: blocked
slice_type: AFK
labels:
  - ready-for-agent
parent: 2026-05-20-prd-yaml-category-registry-and-leaf-category-review-flow.md
blocked_by:
  - ISSUE-019
created: 2026-05-20
---

# Gate Category Memory And Document Leaf Category Lifecycle

## Parent

[PRD: YAML Category Registry And Leaf Category Review Flow](./2026-05-20-prd-yaml-category-registry-and-leaf-category-review-flow.md)

## What To Build

Align Category Memory, reports, and documentation with the new parent/leaf category lifecycle. Learning should only target valid leaf categories in the YAML registry, and operator docs should explain how to add a missing leaf category during manual review.

## Acceptance Criteria

- [ ] Category Memory learning validates against YAML leaf categories.
- [ ] Learning skips parent rows, derived rows, missing categories, and non-leaf targets.
- [ ] Learning can proceed for a newly registered leaf category after registry validation succeeds.
- [ ] Reports distinguish existing manual category decisions from new leaf category registrations.
- [ ] The monthly workflow documents `manual_category`, `new_parent_category`, `new_leaf_category`, and `learn_to_memory`.
- [ ] Project overview glossary uses Parent/Section Row and Leaf Category Row terminology.
- [ ] Agent context and domain language documents record the category registry decision.
- [ ] Data contracts describe the new review columns and category registry behavior.
- [ ] Documentation tests cover the updated workflow terms.
- [ ] Tests cover Category Memory skip/learn behavior for existing leaves, new leaves, parent rows, and missing categories.

## Blocked By

- [ISSUE-019: Plan And Commit Workbook Leaf Row Insertion](./2026-05-20-issue-019-plan-and-commit-workbook-leaf-row-insertion.md)
