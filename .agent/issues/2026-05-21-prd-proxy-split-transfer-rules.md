---
type: prd
id: PRD-2026-05-21-PROXY-SPLIT-TRANSFER-RULES
title: Proxy Split Transfer Rules
status: done
labels:
  - done
created: 2026-05-21
---

# Proxy Split Transfer Rules

## Problem Statement

The monthly tracker currently treats each bank statement transaction as one categorization unit. That blocks a common real workflow: the tracker owner sends one larger payment to Revolut, then uses Revolut to split fixed family support payments to Dad and Mom. In the Tracker Workbook, those are separate Leaf Category Rows, but the Nordea Bank Statement only shows one Revolut cash movement.

If the Revolut transfer is categorized as one ordinary transaction, the tracker owner must either manually split it outside the workflow, categorize the whole transfer to one row, or leave the fixed Dad/Mom amounts unresolved every month. That undermines the monthly dry-run workflow because the same predictable family allocations keep appearing as manual review work.

The owner also wants the review workbook to be easier to use. The current Review Required sheet places `manual_category`, `new_parent_category`, `new_leaf_category`, and `learn_to_memory` far from the transaction description, which makes manual classification harder as more audit columns are added.

## Solution

Introduce Proxy Split Transfer rules. A proxy split rule can match one intermediary transaction, such as a Revolut expense, and carve out configured allocations to multiple Leaf Category Row targets while preserving the original bank transaction for audit.

The Revolut family split rule should be stored in private local config because it contains personal intermediary details and fixed family amounts. The configured allocations are source-currency Proxy Split Base Amounts converted into Tracker Currency with a user-maintained Proxy Split Conversion Rate. For the current family workflow, Dad receives `8000 * 0.82 = 6560 DKK`, Mom receives `4000 * 0.82 = 3280 DKK`, and the total fixed allocation is `9840 DKK`.

The rule should trigger only for an expense/payment to Revolut whose absolute amount can cover the full fixed allocation total. An exact `9840 DKK` transfer should produce Dad and Mom allocation lines with no residual. A larger transfer should produce Dad and Mom allocation lines plus a Residual Review Line for the leftover amount. A smaller transfer should remain review-only. The recurring family split should apply at most once per Reporting Month; if multiple Revolut candidates match, the run should require review instead of double-counting Dad and Mom.

The categorized outputs should keep the original Revolut transaction as a Proxy Split Source Line for audit, excluded from direct workbook totals, and add deterministic Proxy Split Allocation Lines for Dad and Mom. Residual lines should get stable source-derived IDs so Monthly Review Decisions can categorize the leftover for the current month. Residual review decisions should not be learned into Category Memory because a residual is a leftover allocation, not a stable Merchant Identity.

The Review Required workbook should move editable review decision columns close to transaction descriptions and add split metadata without pushing the main classification controls far right.

## User Stories

1. As the tracker owner, I want a single Revolut transfer to allocate fixed Dad and Mom amounts, so that the workbook reflects the actual family support split.
2. As the tracker owner, I want the original Revolut source transaction kept visible, so that I can audit where the split came from.
3. As the tracker owner, I want the original Revolut source transaction excluded from direct workbook totals, so that the split does not double-count expenses.
4. As the tracker owner, I want Dad to receive `8000 * 0.82`, so that the recurring fixed support amount is calculated consistently.
5. As the tracker owner, I want Mom to receive `4000 * 0.82`, so that the recurring fixed support amount is calculated consistently.
6. As the tracker owner, I want `0.82` treated as a configured fixed conversion rate, so that monthly runs are reproducible.
7. As the tracker owner, I want the fixed family amounts stored in private local config, so that personal details do not enter tracked config.
8. As the tracker owner, I want a Revolut transfer smaller than the fixed allocation total to stay review-only, so that the tool does not partially allocate family support.
9. As the tracker owner, I want an exact `9840 DKK` Revolut transfer to be fully allocated, so that no unnecessary residual review row appears.
10. As the tracker owner, I want a larger Revolut transfer to expose only the leftover amount for review, so that I can categorize the remaining Revolut use separately.
11. As the tracker owner, I want residual review rows tied to the original source transaction, so that I know which transfer created the leftover.
12. As the tracker owner, I want residual decisions to apply only to the current month, so that leftover Revolut usage does not become unsafe future Category Memory.
13. As the tracker owner, I want the recurring family split to apply at most once per Reporting Month, so that Dad and Mom are not double-counted.
14. As the tracker owner, I want multiple matching Revolut candidates to require review, so that ambiguous monthly transfers are not silently split.
15. As the tracker owner, I want split allocation and residual lines to have stable IDs, so that reviewed residual decisions can be reused within the same transaction ID scheme.
16. As the tracker owner, I want split metadata in review outputs, so that I can see the split rule, source transaction, role, allocated amount, and residual amount.
17. As the tracker owner, I want review decision columns closer to the transaction description, so that manual categorization is easier.
18. As the tracker owner, I want workbook safety checks to remain authoritative, so that split allocations cannot overwrite populated, formula-owned, fixed, or unsafe cells.
19. As the tracker owner, I want dry-run reports to show proxy split behavior, so that I can review allocations before commit mode.
20. As the tracker owner, I want audit logs to show proxy split source and allocation records, so that the split remains traceable.
21. As a developer, I want proxy split config validation, so that split targets must be valid Leaf Category Rows.
22. As a developer, I want decimal allocation math, so that rounding and residual handling are deterministic.
23. As a developer, I want synthetic tests for exact, larger, smaller, and duplicate Revolut scenarios, so that real financial data stays ignored.
24. As a developer, I want residual Category Memory learning blocked, so that residual rows cannot poison future matching.
25. As a developer, I want review workbook import compatibility, so that older reviewed workbooks continue to apply where possible.

## Implementation Decisions

- Use **Proxy Split Transfer** for one source transaction that intentionally backs multiple tracker category allocations.
- Use **Proxy Split Source Line** for the original bank statement transaction retained for audit and excluded from direct workbook totals.
- Use **Proxy Split Allocation Line** for counted Dad and Mom allocation lines.
- Use **Residual Review Line** for leftover proxy split amounts that require current-month categorization.
- Store concrete Revolut family split rules in private local config, not tracked default rules.
- Validate configured allocation targets against the Category Registry and require Leaf Category Row targets.
- The family split rule matches a Revolut expense/payment and requires the source amount to cover all configured allocations.
- Dad allocation is a Proxy Split Base Amount of `8000` multiplied by a Proxy Split Conversion Rate of `0.82`.
- Mom allocation is a Proxy Split Base Amount of `4000` multiplied by a Proxy Split Conversion Rate of `0.82`.
- Converted allocation amounts are Tracker Currency values in DKK.
- Allocation math uses decimal arithmetic.
- Each converted allocation is rounded to 2 decimal places before residual calculation.
- Residual is calculated from the absolute source transaction amount minus rounded allocation amounts.
- A residual below `0.01 DKK` is zero.
- A negative residual means the rule does not apply and the transaction remains review-only.
- An exact fixed-allocation transfer produces only Dad and Mom allocation lines.
- A larger transfer produces Dad and Mom allocation lines plus a Residual Review Line.
- A smaller transfer remains review-only.
- The recurring family split rule applies at most once per Reporting Month.
- Multiple matching Revolut candidates require review instead of automatic splitting.
- Split allocation and residual IDs are derived from source transaction ID, split rule name, and split role.
- Residual review decisions apply to the current monthly run only.
- Residual review decisions should not be imported into Category Memory.
- The Review Required sheet should place `manual_category`, `new_parent_category`, `new_leaf_category`, and `learn_to_memory` immediately after the core transaction context.
- Split metadata should be present in review outputs but should not push primary review decision columns far right.
- Workbook planning should aggregate counted split allocation lines by category and exclude source lines from direct totals.
- Commit mode remains unchanged in principle: only safe planned writes to copied workbooks are written.

## Testing Decisions

- Tests should verify external behavior through config loading, pipeline dry-run output, categorized CSV/review workbook output, reviewed decision application, category-memory import, workbook planning, report output, and audit output.
- Proxy split config tests should cover valid rules, invalid leaf targets, invalid amounts, invalid rates, and local override loading.
- Pipeline tests should cover exact Revolut split, larger Revolut split with residual, smaller Revolut transaction review-only behavior, and duplicate candidate review behavior.
- Workbook planning tests should prove counted allocation lines contribute to Dad and Mom totals while the source line does not double-count.
- Review workbook tests should cover preferred column ordering, split metadata columns, residual review rows, and old workbook compatibility.
- Category Memory tests should cover residual decisions being skipped while ordinary leaf decisions still learn.
- Report and audit tests should cover source line visibility, allocation line visibility, residual review visibility, and applied conversion-rate formula reporting.
- Tests should use synthetic transactions and workbooks only.

## Out of Scope

- Reading itemized Revolut statements.
- Connecting to a Revolut API.
- Live exchange-rate lookup.
- Automatically inferring split amounts from Revolut behavior.
- General-purpose arbitrary transaction splitting UI.
- Learning residual split decisions into Category Memory.
- Applying the family split more than once per Reporting Month without review.
- Moving private family amounts into tracked default config.
- Changing workbook commit safety rules.
- Investment statement ingestion.

## Further Notes

This PRD comes from a grilling session on the owner's real Revolut workflow. The critical domain distinction is that the Nordea statement proves one cash movement to Revolut, while the tracker owner wants configured, explicit proxy allocations to Dad and Mom. The feature should preserve auditability instead of pretending the bank produced separate Dad and Mom transactions.

The review workbook UX improvement is part of this PRD because proxy split metadata would otherwise make an already wide review sheet harder to use.
