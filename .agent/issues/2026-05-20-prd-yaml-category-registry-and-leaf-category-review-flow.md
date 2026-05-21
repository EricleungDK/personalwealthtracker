---
type: prd
id: PRD-2026-05-20-YAML-CATEGORY-REGISTRY-LEAF-REVIEW
title: YAML Category Registry And Leaf Category Review Flow
status: done
labels:
  - done
created: 2026-05-20
---

# YAML Category Registry And Leaf Category Review Flow

## Problem Statement

The manual review workbook currently lets the tracker owner choose `manual_category` values from workbook row labels. In practice, the workbook includes parent or section rows such as `Insurance`, `Living expenses`, and other totals that are not valid transaction categories. The owner wants to classify transactions to leaf category rows under those parents, such as `Rent`, `Mom`, `Dad`, or `Shopping`.

When the desired leaf category does not exist yet, the current review workflow has no safe way to request it. The user either has to select an invalid parent row, manually edit the tracker workbook outside the workflow, or delay classification until a new category is created by hand.

The project also needs a single durable source of category truth. The workbook is the financial target and review context, but category structure should live in YAML so the tool can validate parent rows, leaf rows, allowed child placement, duplicates, review dropdowns, and future category-memory learning consistently.

## Solution

Introduce a YAML-backed category registry with explicit parent and leaf semantics. Parent or section rows can be declared as allowing leaf children, while calculated totals and other derived rows remain blocked from receiving new transaction categories. Existing flat category data remains supported during migration, but the registry becomes the durable category source.

Extend the manual review workbook so `manual_category` is used for existing leaf category rows only, while missing categories are requested through separate `new_parent_category` and `new_leaf_category` columns. The reviewed second run validates those requests, registers approved new leaf categories in YAML, and applies the current-month review decision to the new leaf category. This category registry update is allowed during the reviewed second run even when workbook value commit is not requested; workbook financial values still require normal commit mode.

When a newly registered leaf category does not exist in the tracker workbook, the workbook planner should produce a structure-change plan. Commit mode should insert the new leaf row under the selected parent in a copied workbook only when formatting, placement, and formulas can be updated safely. If formula updates are ambiguous, the run should block the workbook structure commit and report the required manual adjustment.

Category Memory may learn a transaction mapped to a new leaf category only after that category exists in the YAML registry and passes the same leaf-category validation as any other manual decision.

## User Stories

1. As the tracker owner, I want parent rows such as `Living expenses` and `Insurance` treated as sections, so that I do not accidentally classify transactions to totals.
2. As the tracker owner, I want leaf rows such as `Rent`, `Mom`, `Dad`, and `Shopping` treated as valid categories, so that my manual decisions write to the right workbook rows.
3. As the tracker owner, I want to request a missing leaf category during manual review, so that I do not have to leave the review workflow to fix my category list.
4. As the tracker owner, I want to choose the parent row for a new leaf category, so that the category is placed under the correct section.
5. As the tracker owner, I want the tool to reject new categories under parent rows that do not allow children, so that totals such as `Total net worth` are not corrupted.
6. As the tracker owner, I want YAML to become the durable category registry, so that there is one source of category structure.
7. As the tracker owner, I want the reviewed second run to update YAML with validated new leaf categories, so that future dry runs immediately know the category.
8. As the tracker owner, I want workbook value dry runs to remain safe, so that registering a category does not silently write financial values to the workbook.
9. As the tracker owner, I want new category requests to reject duplicates, so that `Shopping` and `shopping` cannot become separate categories by accident.
10. As the tracker owner, I want `manual_category` to stay focused on existing leaf categories, so that old and new review semantics stay clear.
11. As the tracker owner, I want `new_parent_category` to offer only valid parent rows, so that I do not have to remember which rows can receive leaf categories.
12. As the tracker owner, I want `new_leaf_category` to preserve the exact display label I enter, so that the workbook category name remains human-readable.
13. As the tracker owner, I want aliases to remain explicit, so that adding a new category does not create hidden synonym behavior.
14. As the tracker owner, I want old review workbooks to remain importable, so that existing monthly review decisions do not break.
15. As the tracker owner, I want a report section for requested category additions, so that I can see what changed in YAML and what workbook structure still needs work.
16. As the tracker owner, I want the workbook row insertion planned before commit, so that I can review where a new leaf row will be added.
17. As the tracker owner, I want new workbook leaf rows inserted under the selected parent, so that the workbook structure mirrors the category registry.
18. As the tracker owner, I want row formatting copied from a nearby sibling leaf row, so that newly inserted rows look consistent.
19. As the tracker owner, I want parent formulas updated only when the range is safe to update, so that the workbook is not silently damaged.
20. As the tracker owner, I want ambiguous formula updates blocked with a clear reason, so that I can fix the workbook manually if needed.
21. As the tracker owner, I want Category Memory learning blocked for missing categories, so that future automation does not learn invalid targets.
22. As the tracker owner, I want Category Memory learning allowed after a new leaf category is registered, so that the same merchant can be recognized next month.
23. As a developer, I want parent and leaf semantics represented in config, so that category validation is testable without loading a real workbook.
24. As a developer, I want review import behavior to validate mutually exclusive `manual_category` and new-category columns, so that contradictory reviewed rows fail clearly.
25. As a developer, I want synthetic tests for registry migration, review workbook generation, reviewed-run registration, workbook insertion planning, and memory learning, so that real finance data stays ignored.
26. As a developer, I want docs updated with parent/leaf terminology, so that future agents do not call section rows subcategories.

## Implementation Decisions

- Use **Parent/Section Row** for rows that group or total other workbook rows.
- Use **Leaf Category Row** for transaction categories that can receive source-backed monthly values.
- Keep `manual_category` as the current-month category decision for existing leaf categories.
- Add `new_parent_category` and `new_leaf_category` review columns for missing leaf categories.
- Treat `manual_category` and `new_leaf_category` as mutually exclusive on one review row.
- A reviewed row with a new leaf category must specify a parent row that is explicitly allowed to receive children.
- Parent rows that are derived totals may appear in context sheets, but they must not be valid manual transaction categories.
- Introduce a YAML category registry that can represent parent rows, leaf children, and whether a parent allows new leaf children.
- Preserve backwards compatibility for existing flat `categories` and `aliases` while the tree-shaped registry is introduced.
- Use case-insensitive trimmed matching to detect duplicate category labels while preserving the exact display label in YAML and reports.
- Do not auto-create aliases when a new leaf category is registered.
- The reviewed second run may update `config/categories.yaml` with validated new leaf categories. This is a category-registry update, not a workbook financial value write.
- Category registry updates should be deterministic, auditable, and reversible through normal version control.
- Workbook financial values remain governed by existing dry-run and commit semantics.
- If a newly registered leaf category is missing from the tracker workbook, plan a workbook structure change rather than silently treating the workbook as valid.
- Commit mode may insert missing leaf category rows only into a copied workbook.
- Workbook row insertion should place a new leaf row under its selected parent after existing sibling leaf rows and before the next parent or section boundary.
- Formatting should be copied from a nearby sibling leaf row under the same parent when possible.
- Parent formulas should be updated only when the current range pattern can be identified safely.
- Ambiguous formula or section-boundary detection should block the workbook structure commit and report a manual adjustment.
- Category Memory learning should validate against the YAML leaf registry and skip missing, parent, derived, or otherwise invalid category targets.
- Older reviewed workbooks without `new_parent_category` and `new_leaf_category` should continue to import using the existing `manual_category` behavior.

## Testing Decisions

- Tests should verify external behavior through config loading, review workbook output, reviewed decision import, pipeline dry-run output, workbook planning/commit-to-copy, and category-memory import.
- Registry tests should cover parent rows, leaf rows, allowed child creation, blocked parent rows, duplicate detection, alias preservation, and flat-category compatibility.
- Review workbook tests should cover new columns, parent dropdown values, leaf category dropdown values, category option metadata, and old workbook compatibility.
- Reviewed-run tests should cover registering a new leaf category into YAML, preserving exact display labels, rejecting duplicates, rejecting invalid parents, and rejecting rows that fill both `manual_category` and `new_leaf_category`.
- Pipeline tests should prove that the reviewed second run can classify the current transaction to a newly registered leaf category.
- Workbook tests should cover missing leaf row planning, row insertion into a copied workbook, sibling formatting copy, safe formula updates, and blocked ambiguous formula updates.
- Category Memory tests should cover learning after leaf registration and skipping missing, parent, derived, or non-leaf targets.
- Documentation tests should cover the updated monthly workflow and glossary terms.

## Out of Scope

- A graphical category editor.
- LLM-suggested category creation.
- Automatic alias generation.
- Generic workbook restructuring beyond inserting reviewed leaf category rows.
- Writing financial workbook values during plain dry-run behavior.
- Automatically fixing ambiguous workbook formulas.
- Moving real tracker workbook data or personal categories into committed fixtures.
- Investment statement support.

## Further Notes

This PRD came from a grilling session about the manual review workbook. The key terminology correction is that workbook section rows are parent or section rows, not subcategories. The desired category target is a leaf category row under a parent section.

The owner explicitly wants YAML to become the durable category source, with validated new categories added by the reviewed second run so future runs do not rely on two separate category sources.
