---
type: issue
id: ISSUE-024
title: Reorder Review Workbook And Add Split Metadata
status: done
slice_type: AFK
labels:
  - done
parent: 2026-05-21-prd-proxy-split-transfer-rules.md
blocked_by:
  - ISSUE-021
created: 2026-05-21
---

# Reorder Review Workbook And Add Split Metadata

## Parent

[PRD: Proxy Split Transfer Rules](./2026-05-21-prd-proxy-split-transfer-rules.md)

## What To Build

Improve the Review Required workbook so transaction context and editable decision columns are adjacent, then add proxy split metadata columns without making the classification workflow harder to scan. Normal review rows should remain compatible, and older reviewed workbooks should still import where their existing columns are present.

## Acceptance Criteria

- [x] Review Required column order starts with transaction context followed immediately by `manual_category`, `new_parent_category`, `new_leaf_category`, and `learn_to_memory`.
- [x] Preferred review column order includes split role, split rule, source transaction ID, allocated amount, and residual amount after the primary decision columns.
- [x] Workbook safety and diagnostic columns are moved farther right.
- [x] Existing review workbook dropdowns still apply to the correct columns after reordering.
- [x] Existing reviewed workbooks generated before the reorder remain importable by header name.
- [x] Proxy split allocation and residual rows expose enough metadata to identify the source transaction and split role.
- [x] Normal non-split rows leave split metadata blank.
- [x] Tests cover header ordering, dropdown ranges, old workbook import compatibility, split metadata values, and normal row blanks.

## Blocked By

- [ISSUE-021: Add Proxy Split Exact Allocation Dry Run](./2026-05-21-issue-021-add-proxy-split-exact-allocation-dry-run.md)
