---
type: issue
id: ISSUE-016
title: Introduce YAML Category Registry
status: done
slice_type: AFK
labels:
  - done
parent: 2026-05-20-prd-yaml-category-registry-and-leaf-category-review-flow.md
blocked_by: []
created: 2026-05-20
---

# Introduce YAML Category Registry

## Parent

[PRD: YAML Category Registry And Leaf Category Review Flow](./2026-05-20-prd-yaml-category-registry-and-leaf-category-review-flow.md)

## What To Build

Add a YAML-backed category registry that distinguishes parent or section rows from leaf category rows. The registry should become the durable source of category structure while preserving compatibility with the current flat category list and aliases.

## Acceptance Criteria

- [x] Category config can represent parent rows, leaf child rows, and whether a parent allows new leaf children.
- [x] Existing flat `categories` and `aliases` remain loadable for backwards compatibility.
- [x] Loaded config exposes the valid leaf category set separately from parent/section rows.
- [x] Loaded config exposes parent rows that are allowed to receive new leaf children.
- [x] Derived totals and blocked parent rows are not valid manual transaction categories.
- [x] Duplicate category labels are detected case-insensitively after trimming whitespace.
- [x] Exact category display labels are preserved.
- [x] Alias loading remains explicit and does not auto-create aliases for new leaf categories.
- [x] Tests cover tree-shaped config, flat config compatibility, duplicate detection, parent/leaf lookup, and alias preservation.

## Blocked By

None - can start immediately.
