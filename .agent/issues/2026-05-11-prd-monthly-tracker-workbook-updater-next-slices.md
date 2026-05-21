---
type: prd
title: Monthly Tracker Workbook Updater Next Slices
status: blocked
labels:
  - blocked
created: 2026-05-11
source: .agent/Tasks/context.md grilling session results
---

# PRD: Monthly Tracker Workbook Updater Next Slices

## Problem Statement

The current PersonalWorthTracker MVP can parse a Nordea bank statement, categorize transactions with deterministic rules, plan safe workbook updates, and write eligible values to a copied tracker workbook. The next problem is that the updater still treats the workbook too generically: it does not yet fully understand which rows are source-backed leaf rows, which rows are formula-owned derived rows, how to learn from reviewed categorization decisions, how to create missing reporting periods safely, or how future investment statement evidence should fit into one monthly plan.

The user needs the automation to stay aligned with the existing tracker workbook instead of becoming a personal finance ledger. It should reduce monthly manual work while preserving workbook formulas, manual values, privacy boundaries, and reviewability.

## Solution

Build the next implementation slices around the resolved domain model:

- Treat the product as a **Monthly Tracker Workbook Updater**, not a ledger.
- Preserve the **Tracker Workbook** as the source of truth.
- Write only source-backed **Leaf Workbook Row** values when workbook safety checks pass.
- Never directly write **Derived Workbook Row** values or section totals.
- Add **Category Memory** that learns only from **Confirmed Review Decision** records imported from a reviewed file.
- Add safe **Period Column** and **Year Block** creation as explicit, reviewable **Planned Structure Change** records.
- Keep Nordea cashflow evidence, investment valuation evidence, and workbook-derived formulas as separate sources of authority.
- Keep reports and audit logs rich enough to explain workbook writes, skipped updates, review items, structure changes, learned mappings, conversion rates, and cross-source mismatches.

## User Stories

1. As the tracker owner, I want the updater to preserve my existing workbook structure, so that automation improves my workflow without replacing my tracker.
2. As the tracker owner, I want manual workbook values to take priority over calculated statement totals, so that automation never silently overwrites my decisions.
3. As the tracker owner, I want the reporting month to be explicit, so that I can backfill missed months safely.
4. As the tracker owner, I want formula-owned rows to be protected, so that workbook calculations stay intact.
5. As the tracker owner, I want section totals to remain derived, so that totals are calculated consistently by the workbook.
6. As the tracker owner, I want `Income (net)` to remain formula-owned, so that parent income totals are not overwritten by automation.
7. As the tracker owner, I want matched Nordea salary deposits to update `Full-time job (net)` when safe, so that net salary entry can be automated.
8. As the tracker owner, I want multiple salary-like deposits to require review, so that bonuses or false matches are not silently written.
9. As the tracker owner, I want tax and labour contribution rows to preserve workbook formulas/manual logic, so that the updater does not invent payroll breakdowns from a bank deposit.
10. As the tracker owner, I want recurring pre-filled workbook values to remain untouched during monthly updates, so that expected fixed values are not overwritten.
11. As the tracker owner, I want observed recurring payments to be reported as confirmations or differences, so that I can spot changed fixed costs.
12. As the tracker owner, I want internal transfers excluded from generic income and expenses, so that moving money between owned accounts is not counted as spending.
13. As the tracker owner, I want investment contributions to remain cashflow, so that transfers to investing are not confused with current asset value.
14. As the tracker owner, I want credit card settlements treated as liability movement, so that credit card payments are not double-counted as expenses.
15. As the tracker owner, I want itemized card purchases to be a separate future source, so that card spending is only categorized when actual purchase evidence exists.
16. As the tracker owner, I want deterministic category matches to be the only auto-write candidates, so that ambiguous transactions stay review-only.
17. As the tracker owner, I want unmatched transactions to appear in review outputs, so that I can make categorization decisions deliberately.
18. As the tracker owner, I want category memory to learn from my confirmed review decisions, so that repeated merchants become automatic over time.
19. As the tracker owner, I want category memory stored separately from hand-written local rules, so that generated learning remains inspectable and resettable.
20. As the tracker owner, I want learned mappings to use normalized merchant identity, so that changing reference numbers do not break matching.
21. As the tracker owner, I want recurring learned mappings to include optional amount/date hints, so that recurring charges are matched narrowly.
22. As the tracker owner, I want one confirmed review decision to be enough for future categorization, so that I do not repeatedly approve the same merchant.
23. As the tracker owner, I want learning and workbook commit to remain separate commands, so that category-memory changes can be dry-run before writing a workbook.
24. As the tracker owner, I want a reviewed decision file import workflow, so that learning is auditable and testable.
25. As the tracker owner, I want same-month refunds to reduce matched category totals, so that monthly spend reflects net cashflow.
26. As the tracker owner, I want later-month refunds recorded in the month they appear, so that the updater does not reopen prior workbook months.
27. As the tracker owner, I want reimbursements to stay aligned to existing workbook rows, so that the workbook does not gain a more complicated offset model.
28. As the tracker owner, I want deterministic expense claims to map to `Expense claims`, so that reimbursements can be tracked without ledger semantics.
29. As the tracker owner, I want missing month columns to be created eventually, so that I do not manually maintain workbook periods forever.
30. As the tracker owner, I want missing year creation to add a full 12-month block, so that workbook structure stays consistent.
31. As the tracker owner, I want period creation shown in dry-run before commit, so that workbook structure changes are reviewable.
32. As the tracker owner, I want new period columns to copy the immediately previous period column, so that formulas and formatting follow the workbook’s current pattern.
33. As the tracker owner, I want ordinary copied manual values cleared in new periods, so that last month’s actual numbers do not become this month’s data.
34. As the tracker owner, I want carry-forward rows configured separately from fixed rows, so that overwrite protection and value carry-forward are not confused.
35. As the tracker owner, I want only configured carry-forward recurring rows to retain copied values, so that the writer does not infer fixed values from history alone.
36. As the tracker owner, I want investment statements treated as a separate evidence source, so that asset values are not inferred from bank transfers.
37. As the tracker owner, I want investment asset rows updated from month-end market values, so that net worth rows represent point-in-time values.
38. As the tracker owner, I want USD investment values converted to DKK with my fixed rate, so that the DKK tracker can use USD statement data without live FX.
39. As the tracker owner, I want the applied conversion rate recorded in reports and audits, so that past monthly values remain reproducible.
40. As the tracker owner, I do not want conversion-rate metadata written into workbook cells for now, so that the workbook structure stays unchanged.
41. As the tracker owner, I want holding-level investment values mapped to individual asset rows only when explicit, so that the updater does not guess allocations.
42. As the tracker owner, I want total-only investment values mapped only to configured total rows or review, so that individual holdings are not fabricated.
43. As the tracker owner, I want crypto rows out of scope until a dedicated source exists, so that bank or brokerage transfers are not misused as crypto valuation.
44. As the tracker owner, I want Nordea cashflow and investment valuation evidence combined into one monthly planning report, so that I can review one proposed workbook update set.
45. As the tracker owner, I want cross-source mismatches reported for review, so that inconsistent cashflow and investment evidence is visible.
46. As the tracker owner, I want one-off workbook cleanup tasks separate from monthly updates, so that label or structure maintenance does not surprise me during financial runs.
47. As the tracker owner, I want all generated financial outputs to remain local and ignored by Git, so that sensitive data stays private.
48. As a future implementation agent, I want the PRD to separate active tasks from planning backlog, so that I do not accidentally mutate the project’s agent workflow state.

## Implementation Decisions

- Add a workbook row authority model that distinguishes **Leaf Workbook Row**, **Derived Workbook Row**, section total, formula-owned row, fixed/protected row, and carry-forward recurring row.
- Direct workbook value updates must target leaf rows only.
- `Full-time job (net)` can be a direct target for deterministic Nordea net salary deposits when the target cell is otherwise safe.
- `Income (net)`, tax rows, labour contribution rows, section totals, and formula-owned rows must not be direct write targets.
- Salary multi-match handling should calculate the aggregate amount but require review before writing.
- Category aggregation should support netting deterministic refunds against matched categories in the reporting month where the refund appears.
- Cross-month refunds must not reopen prior workbook periods.
- Deterministic expense-claim matches can map to the existing expense claim row, but no separate reimbursement offset model should be introduced.
- Add a category memory module with a small interface for loading memory, matching memory, importing confirmed decisions, and writing memory.
- Category memory should be a private generated store, separate from local hand-written rules.
- Category memory should learn only from confirmed reviewed decisions and never from unconfirmed automatic matches.
- A reviewed decision import command should be separate from monthly dry-run and commit mode.
- A monthly run after learning should be re-run in dry-run before commit.
- Add normalized merchant identity extraction for learned matches.
- Add recurring match hints for amount tolerance and day-window matching when a confirmed decision is recurring.
- One confirmed review decision can produce future review-free categorization, subject to normal workbook safety checks.
- Add period planning as a structure-change model separate from value updates.
- Missing period columns and year blocks should appear in dry-run output as planned structure changes.
- Commit mode may apply planned structure changes only after they are visible in dry-run behavior.
- Missing year creation should add a full 12-month year block when the prior year pattern is unambiguous.
- New periods should copy formulas, styles, widths, merged headers, and relevant structure from the immediately previous period/year block.
- New period creation should clear ordinary copied non-formula values.
- Carry-forward recurring rows should be configured separately from fixed/protected rows.
- Only configured carry-forward recurring rows may retain copied non-formula values during period/year creation.
- Add investment statement evidence as a separate model from normalized bank transactions.
- Investment evidence should represent holding-level values, portfolio total values, source currency, applied conversion rate, and tracker-currency value.
- USD investment values should convert to DKK using a user-maintained fixed conversion rate.
- The applied conversion rate belongs in reports and audit logs, not workbook cells.
- Holding-level investment values may map to individual asset rows.
- Total-only investment values may map only to configured total rows or review.
- Combined monthly planning should merge Nordea cashflow evidence and investment valuation evidence at workbook planning/reporting time.
- Cross-source mismatch records should be review-only and should not let one source override another outside its evidence type.
- Workbook cleanup tasks, such as currency label cleanup, should remain separate from monthly planning and commit mode.
- Generated reports, audit logs, category memory, real statements, and copied workbooks must remain local-only and ignored by Git.

## Testing Decisions

- Tests should focus on external behavior: planned updates, reports, audit records, output files, and copied workbook contents.
- Avoid testing internal helper implementation details except where a parser or matcher has a stable, domain-level contract.
- Add focused workbook planning tests for derived-row skips, leaf-row writes, formula preservation, manual-value precedence, fixed-row protection, and section total protection.
- Add salary planning tests for one matched salary deposit, multiple salary-like deposits requiring review, and derived payroll rows remaining untouched.
- Add category memory tests for reviewed file import, merchant identity matching, recurring hint matching, memory persistence, and no learning from automatic guesses.
- Add pipeline-level tests showing that learning and commit remain separate workflows.
- Add refund tests for same-month deterministic netting, later-month current-period treatment, and unmatched refund review behavior.
- Add claim tests showing deterministic `Expense claims` mapping without offset modelling.
- Add workbook structure tests for missing month planning, missing year-block planning, dry-run structure-change reporting, previous-column copy source, cleared copied manual values, retained carry-forward rows, and ambiguous pattern review.
- Add investment evidence tests for USD-to-DKK conversion, applied conversion rate reporting, holding-level mapping, total-only review, and no crypto automation.
- Add combined planning tests for a monthly run with both Nordea cashflow and investment valuation evidence, including cross-source mismatch reporting.
- Existing test patterns already cover workbook safety planning, commit-to-copy behavior, pipeline dry-run outputs, parser fixtures, categorization rules, and safety failures; the new tests should extend those patterns rather than introduce a separate test style.

## Out of Scope

- Building a personal finance ledger or canonical transaction store.
- Generic multi-bank statement ingestion.
- Live FX lookup or external market-data dependencies.
- LLM categorization as an auto-write source.
- Crypto or digital asset valuation without a dedicated valuation source.
- Direct writes to formula-owned rows or section totals.
- Writing conversion-rate metadata into tracker workbook cells.
- Reopening prior workbook periods for later refunds.
- Combining category learning and workbook commit into one command.
- Replacing the existing workbook format.
- Sending sensitive financial data to external services.

## Further Notes

- This PRD is based on the 2026-05-11 grilling session captured in the project context and domain language docs.
- The issue is intentionally broad. A future `to-issues` pass should split it into implementation issues matching the backlog themes:
  - workbook row authority,
  - category memory learning,
  - period/year creation,
  - refunds and claims,
  - investment statement evidence,
  - combined monthly planning,
  - workbook cleanup tasks.
- The local issue tracker for this repo is `.agent/issues`.
