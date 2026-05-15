# PersonalWorthTracker Context

Last updated: 2026-05-11

## Project State

- Phase: MVP 1 implementation scaffold.
- Framework: Python local CLI.
- Package manager: uv with `pyproject.toml`.
- Product requirements: Defined from `personal_wealth_tracker_project_case_background.md`.
- Implementation status: Nordea PDF-first MVP scaffold implemented and dry-run validated.

## Active Tasks

| Task ID | Status | Owner | Notes |
|---------|--------|-------|-------|
| SETUP-001 | COMPLETE | Codex | Created baseline folder structure and starter guidance files. |
| MVP1-001 | COMPLETE | Codex | Implemented local Nordea PDF parsing, deterministic categorization, safe workbook planning/writing, reports, and tests. |

## Active Delegations

| Sub-Agent | Task ID | Status | Started | Expected Completion |
|-----------|---------|--------|---------|---------------------|

## Decisions

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-05-06 | Use the workspace baseline folder structure. | User requested folder construction based on the workspace `AGENTS.md` template before project details are defined. |
| 2026-05-06 | Build MVP 1 as a Python CLI using uv. | Keeps the workflow local, testable, and easy to extend later. |
| 2026-05-06 | Use Nordea PDF account statements as the first ingestion source. | User provided `bank-statement.pdf`; inspection showed a Nordea `Kontoudskrift` with embedded text and DKK booked amounts. |
| 2026-05-06 | Treat DKK as the MVP tracker currency. | User selected DKK as the tracker currency for MVP processing. |
| 2026-05-06 | Ignore real statements, workbooks, reports, backups, and generated financial data. | The project handles sensitive personal finance data and must not commit local inputs or outputs. |
| 2026-05-06 | Pin local development to Python 3.12. | The project requires Python 3.11+ and the workspace now has Python 3.12.13 plus uv installed. |
| 2026-05-11 | Define the product boundary as a monthly tracker workbook updater, not a personal finance ledger. | The existing workbook remains the source of truth; the automation proposes safe monthly category updates from statement data rather than modelling cross-month financial events. |
| 2026-05-11 | Treat the reporting month as an explicit user-selected period for MVP 1. | Backfills and reruns should be predictable; a future scheduler can default to the previous calendar month without changing the core domain concept. |
| 2026-05-11 | Existing manual workbook values take priority over newly calculated statement totals. | The updater is an assistant for the tracker workbook, so populated cells are review-only instead of being silently overwritten. |
| 2026-05-11 | Split statement sources by evidence type: bank statements prove cash movement, investment statements prove asset values or holdings. | A cash transfer to investing is not the same as current portfolio value; asset rows should come from investment/balance sources rather than bank transaction rows. |
| 2026-05-11 | Investment asset rows should use month-end market value, while investment contributions remain cashflow. | Net worth rows need point-in-time asset valuation; contribution amounts are useful cash movement but do not prove current holding value. |
| 2026-05-11 | Exclude internal transfers from income and expense totals by default, except when they intentionally map to a tracker cashflow row. | Moving money between owned accounts is not spending or income, but planned allocations such as investment contributions can still be tracked as cashflow. |
| 2026-05-11 | Treat credit card payments as liability settlement, not expenses. | The credit card payment is already counted in the liability area; expense categorization should come from itemized card transactions if those are ingested later. |
| 2026-05-11 | Leave pre-filled recurring workbook values untouched. | Observed recurring payments should confirm or flag differences for review rather than overwrite fixed/manual cells. |
| 2026-05-11 | Auto-write only high-confidence deterministic category matches. | Ambiguous, fuzzy, or unmatched transactions are safer as review-only suggestions than silent workbook updates. |
| 2026-05-11 | Auto-learning should learn only from confirmed review decisions for now. | The automation should improve from user-approved categorization choices, not reinforce its own unconfirmed guesses. |
| 2026-05-11 | Store learned category memory separately from hand-written local rules. | `config/rules.local.yaml` remains curated private config; generated confirmed mappings belong in ignored category memory under `data/category_memory/`. |
| 2026-05-11 | Learned category memory should match on normalized merchant identity, with optional amount/date hints for recurring payments. | Full descriptions are fragile and may contain sensitive changing references; recurring decisions need enough constraints to avoid overbroad matches. |
| 2026-05-11 | One confirmed review decision is enough for future review-free categorization from category memory. | Automation value depends on not repeatedly asking for the same decision; workbook write safety remains governed by the normal cell, formula, fixed-row, period, and confidence checks. |
| 2026-05-11 | Confirmed review decisions should be imported from a reviewed CSV through a separate learning command. | Keeping learning separate from dry-run/commit processing preserves auditability and makes the workflow testable before interactive review exists. |
| 2026-05-11 | Keep learning and workbook commit as separate workflow steps. | Category memory changes should be visible in a follow-up dry run before any workbook copy is written. |
| 2026-05-11 | Treat Nordea as the only bank statement source for now; add investment account statement support as a separate source type later. | The user currently has one Nordea bank statement and will provide a distinct investment account statement, so near-term scope is not generic multi-bank ingestion. |
| 2026-05-11 | A future monthly planning run should combine Nordea bank statement evidence and investment account statement evidence for the same reporting month. | The monthly report should present one proposed workbook update set, while each source type keeps its own parser and data contract. |
| 2026-05-11 | Do not let Nordea and investment statements override each other outside their evidence type; flag cross-source mismatches for review. | Cashflow and investment valuation records can corroborate each other, but disagreement should be visible rather than silently reconciled. |
| 2026-05-11 | Convert USD investment statement values to DKK using a user-maintained fixed conversion rate. | Investment statements are expected to report USD values, while the tracker is DKK; MVP should avoid live FX dependencies and use an explicit configured rate instead. |
| 2026-05-11 | Record the fixed conversion rate used for each reporting month in report and audit outputs. | A global configured default is acceptable, but each monthly update must be reproducible after the default rate changes. |
| 2026-05-11 | Do not write conversion-rate metadata into the tracker workbook for now. | The workbook should receive only the converted DKK values; report/audit outputs carry the FX assumption without reshaping the workbook. |
| 2026-05-11 | Investment statements may update individual asset rows only when holding-level month-end values are explicit. | If a statement provides only total account value, the updater should use a mapped total row or report for review rather than guessing allocation across holdings. |
| 2026-05-11 | Keep crypto and other digital asset rows out of scope until a dedicated valuation source exists. | Bank and investment account statements should not be used to infer crypto values from transfers or unrelated holdings. |
| 2026-05-11 | Tracker workbook currency labels and assumptions should be DKK. | The user does not currently see an EUR label, and any currency labels in this workbook context should align with the DKK tracker policy. |
| 2026-05-11 | Correcting workbook currency labels is a separate one-off cleanup task, not part of monthly update runs. | Label/text maintenance changes workbook structure assumptions and should not be mixed with financial value updates. |
| 2026-05-11 | The updater should eventually create missing month/year columns in the tracker workbook. | Monthly automation should not require manual column setup, but column creation must preserve formulas, formatting, merged headers, and workbook structure. |
| 2026-05-11 | Missing period-column creation must be shown in dry-run output before commit mode creates it. | Creating month/year columns is a workbook structure change and should be explicitly reviewable before a copied workbook is modified. |
| 2026-05-11 | New period columns should copy formulas and formatting from the immediately previous period column. | The existing workbook is the best template; dry-run should report which source column will be copied. |
| 2026-05-11 | Creating a missing year should add the full 12-month year block at once when the workbook pattern is clear. | The tracker is organized by year/month blocks, so a full-year structure avoids repeated monthly structural edits; ambiguous patterns should stop for review. |
| 2026-05-11 | New period/year columns should preserve structure and formulas but clear ordinary copied manual values. | Copying prior actual values into a new month would create false financial data; formulas, styles, widths, and intended fixed/pre-filled logic need explicit handling. |
| 2026-05-11 | New period/year creation may carry forward only explicitly configured pre-filled recurring rows. | The writer should not infer fixed recurring content from previous values alone; all other copied non-formula values must be cleared. |
| 2026-05-11 | Configure carry-forward rows separately from fixed/protected rows. | `fixed_rows` protects cells from overwrite, while `carry_forward_rows` authorizes retaining copied recurring values during period creation. |
| 2026-05-11 | Nordea statements can support net salary income, while payroll/tax derived workbook rows should be preserved as formulas or manual workbook logic. | Workbook inspection showed formula-driven payroll/tax rows, so the updater should not add a salary statement source unless this need reappears later. |
| 2026-05-11 | Write matched Nordea net salary deposits only to the `Full-time job (net)` row when workbook safety checks pass. | The bank statement proves net salary cash-in; derived rows such as `Income (net)`, `Taxes`, and labour contribution logic belong to workbook formulas/manual logic. |
| 2026-05-11 | `Income (net)` is a derived workbook row and must not be directly written by the updater. | Workbook inspection showed `Income (net)` aggregates underlying rows, so direct writes would conflict with workbook formulas. |
| 2026-05-11 | Section total rows are derived workbook rows and must not be directly written by the updater. | Rows such as `Cashflow`, `Recurring payments`, `Living expenses`, `Services`, `Insurance`, `Investments`, `Assets`, and `Total net worth` should be calculated by workbook formulas/structure from evidence-backed leaf rows. |
| 2026-05-11 | Multiple salary-like deposits in one reporting month should be summed but require review before writing. | Multiple salary deposits can be legitimate but may indicate a false match, so the report should show the component deposits and keep the write review-only. |
| 2026-05-11 | Same-month refunds may reduce the matched expense category only when the refund category match is deterministic. | Monthly category totals should net source-backed refunds against spending, but vague or unmatched refunds remain review-only. |
| 2026-05-11 | Later-month refunds reduce the current reporting month's matched category and do not reopen prior months. | The product is a monthly workbook updater, not a ledger, so cashflow is recorded in the month it appears on the statement. |
| 2026-05-11 | Keep reimbursement/expense-claim handling aligned to existing workbook rows without adding a richer offset model. | Identifiable claims can map to the existing `Expense claims` row when deterministic; otherwise they remain normal review items. |
| 2026-05-11 | End the documentation grilling session and preserve its results in a separate planning block. | `.agent/Tasks/context.md` also supports a separate agent workflow, so grilling backlog items should not be mixed into the `Active Tasks` table until intentionally promoted. |

## Open Questions

- Private category rules can be expanded in ignored `config/rules.local.yaml` after reviewing dry-run outputs.
- Missing year/month column creation needs a workbook writer design that safely preserves formulas, formatting, merged headers, and section structure.
- Commit mode on the real local workbook still needs manual review of dry-run output before use.
- Any workbook label cleanup needed to align visible currency text with DKK should be handled as a separate one-off task.
- Investment account statement support needs a separate ingestion contract before asset rows such as JEPI, OXY, or portfolio balances are automated.
- Crypto/digital asset automation needs a separate dedicated valuation source before it is in scope.
- USD-to-DKK conversion policy needs exact configuration shape and reporting/audit fields before investment statement support is implemented.

## Grilling Session Results

Session date: 2026-05-11

Purpose: stress-test the PersonalWorthTracker domain model and convert resolved decisions into a planning backlog.

Scope note: this section is planning context only. It does not modify the `Active Tasks` table above. Promote items from this section into the active workflow only when work is intentionally scheduled.

### Resolved Boundaries

- Product boundary: **Monthly Tracker Workbook Updater**, not a personal finance ledger.
- Workbook authority: existing manual workbook values win; statement totals are advisory when a target cell is populated.
- Reporting period: **Reporting Month** is explicit for MVP 1.
- Evidence sources: Nordea proves bank cashflow; investment account statements prove investment values/holdings; sources do not override each other outside their evidence type.
- Workbook writes: write only evidence-backed leaf rows; never write formula-owned or section total rows directly.
- Salary: Nordea can write matched net salary to `Full-time job (net)` when safe; `Income (net)`, taxes, and labour contribution logic remain workbook-owned.
- Category automation: auto-write only deterministic high-confidence matches; ambiguous/unmatched transactions are review-only.
- Learning: category memory learns only from confirmed reviewed decisions, stored separately under ignored `data/category_memory/`.
- Period creation: missing month/year columns should eventually be created safely, with dry-run review before commit.
- Investment valuation: USD investment values convert to DKK using a user-maintained fixed rate; the applied rate is recorded in report/audit only.
- Refunds/claims: deterministic refunds net in the reporting month where they appear; prior months are not reopened; claims stay aligned to the existing `Expense claims` row.

### Planning Backlog

These backlog items are not active tasks yet.

| Backlog ID | Theme | Scope |
|------------|-------|-------|
| GRILL-BACKLOG-001 | Workbook row authority model | Add explicit derived/leaf row handling; never write section totals or `Income (net)`; allow safe `Full-time job (net)` writes. |
| GRILL-BACKLOG-002 | Category memory learning | Add reviewed CSV import, ignored category memory storage, merchant identity matching, recurring hints, and no self-learning from guesses. |
| GRILL-BACKLOG-003 | Period/year creation | Plan and commit missing period columns/year blocks safely; copy prior structure; clear ordinary manual values; support separate `carry_forward_rows`. |
| GRILL-BACKLOG-004 | Refunds and claims | Net deterministic refunds in the current reporting month; keep vague refunds review-only; map deterministic claims to `Expense claims` without a richer offset model. |
| GRILL-BACKLOG-005 | Investment statement evidence | Define separate investment valuation contract; parse USD month-end values; convert to DKK with fixed rate; map explicit holdings to asset rows. |
| GRILL-BACKLOG-006 | Combined monthly planning | Combine Nordea cashflow and investment valuation evidence into one monthly plan while reporting cross-source mismatches. |
| GRILL-BACKLOG-007 | Workbook cleanup tasks | Keep one-off label/currency cleanup separate from monthly planning and commit mode. |

### Current Non-Goals

- Personal finance ledger semantics.
- Generic multi-bank ingestion.
- Live FX lookup.
- LLM categorization as an auto-write source.
- Crypto/digital asset automation without a dedicated valuation source.
- Direct writes to formula-owned rows or section totals.

## Activity Log

- 2026-05-06: Created baseline project folders and starter files.
- 2026-05-06: Added MVP 1 implementation plan based on Nordea PDF input and DKK workbook policy.
- 2026-05-06: Implemented MVP 1 scaffold, installed Python 3.12 and uv, ran tests, and validated dry-run parsing of the local Nordea PDF.
- 2026-05-06: Created and pushed initial commit `0c0992a feat: initialize wealth tracker automation` to `origin/main`.
- 2026-05-06: Created EOD summary in `docs/Daily_blogpost/2026-05-06.md`.
- 2026-05-07: Added synthetic redacted Nordea PDF fixture generator and public parser integration coverage.
- 2026-05-07: Fixed review findings by validating statement currency, rejecting out-of-period transactions, and preventing footer text from extending the last parsed transaction.
- 2026-05-07: Added ignored local rule overlay support so private merchant categorization can improve without committing personal transaction data.
- 2026-05-07: Added synthetic workbook writer tests for aggregation, safety decisions, and commit-to-copy behavior.
- 2026-05-07: Added full synthetic pipeline integration tests for dry-run outputs and commit-to-copy workbook writes.
- 2026-05-07: Added recurring amount/date categorization support through public config and ignored local rule overlays.
- 2026-05-11: Started `.agent` documentation grilling session and resolved the top-level product boundary as a monthly tracker workbook updater rather than a personal finance ledger.
- 2026-05-11: Resolved **Reporting Month** as the explicit year/month selected for a run, not an implicit calculation from the run date.
- 2026-05-11: Resolved precedence between statement data and populated workbook cells: the existing **Tracker Workbook** value wins by default, and the parsed total is reported for review.
- 2026-05-11: Resolved source boundaries: bank statements update cashflow evidence, while investment statements are needed for asset value or holdings evidence.
- 2026-05-11: Resolved investment statement semantics: **Asset Value Row** updates use **Month-End Market Value**, while contributions remain **Cashflow Row** updates.
- 2026-05-11: Resolved internal transfer handling: owned-account transfers are excluded from generic income/expense totals unless deliberately mapped to a specific **Cashflow Row**.
- 2026-05-11: Resolved credit card payment handling: card settlement payments are liability movement, not expense evidence.
- 2026-05-11: Resolved recurring fixed row handling: pre-filled values stay in the **Tracker Workbook**, while observed payments are reported as confirmation or differences.
- 2026-05-11: Resolved category write confidence: only high-confidence deterministic matches can write to empty cells; ambiguous matches remain review-only.
- 2026-05-11: Resolved auto-learning boundary: future category memory should be created from confirmed review decisions only, not from unreviewed automatic matches.
- 2026-05-11: Resolved category memory storage: learned mappings should live in a separate ignored generated store, not inside `config/rules.local.yaml`.
- 2026-05-11: Resolved category memory matching keys: learn normalized merchant identity by default, with amount/date hints for recurring confirmed decisions.
- 2026-05-11: Resolved category memory trust: one confirmed review decision can produce future review-free categorization, but automatic writes still require all workbook safety checks.
- 2026-05-11: Resolved learning workflow: future CLI should import confirmed decisions from a reviewed CSV using a separate command rather than prompting inline during monthly processing.
- 2026-05-11: Resolved workflow separation: learning from reviewed decisions and committing workbook updates should remain separate commands with a dry-run verification step between them.
- 2026-05-11: Refined source scope: bank-side ingestion remains Nordea-only for now; future investment account statements are a distinct source type, not another bank statement in the same model.
- 2026-05-11: Resolved future source orchestration: one monthly planning run should combine Nordea cashflow evidence and investment account valuation evidence for the same **Reporting Month**.
- 2026-05-11: Resolved cross-source precedence: Nordea cashflow evidence and investment valuation evidence keep separate authority, and mismatches are reported for review.
- 2026-05-11: Resolved investment FX direction: investment statement values are expected in USD and should be converted to DKK using a user-maintained fixed conversion rate, not live FX.
- 2026-05-11: Resolved FX auditability: the configured fixed conversion rate can be global, but every monthly report/audit must record the exact rate used.
- 2026-05-11: Resolved FX workbook scope: applied conversion rates stay in report/audit outputs and are not written into the tracker workbook for now.
- 2026-05-11: Resolved investment row mapping: explicit holding-level values can update matching **Asset Value Row** entries; total-only statements must not be split across assets by guesswork.
- 2026-05-11: Resolved crypto scope: digital asset rows remain out of scope until the user provides a dedicated valuation source.
- 2026-05-11: Resolved tracker currency label ambiguity: the workbook context should be DKK; prior EUR-label note is treated as stale and removed from open questions.
- 2026-05-11: Resolved workbook label cleanup scope: DKK label corrections should be a separate one-off task, not part of monthly updater execution.
- 2026-05-11: Resolved missing period handling direction: the updater should eventually create missing month/year columns, subject to a dedicated safe writer design.
- 2026-05-11: Resolved period-column creation workflow: dry-run should report planned structure changes before commit mode can create missing period columns.
- 2026-05-11: Resolved period-column template source: new month/year columns should copy the immediately previous period column rather than use a separate template column.
- 2026-05-11: Resolved new-year creation behavior: create a full 12-month year block at once when the prior workbook pattern can be confidently copied.
- 2026-05-11: Resolved period-copy semantics: preserve formulas and structure but clear ordinary copied manual values in newly created period columns.
- 2026-05-11: Resolved pre-filled carry-forward rule: only explicitly configured recurring rows may retain copied values during period/year creation; all other non-formula values are cleared.
- 2026-05-11: Resolved carry-forward configuration: use a separate `carry_forward_rows` concept rather than overloading `fixed_rows`.
- 2026-05-11: Resolved payroll evidence boundary after workbook inspection: Nordea can support net salary income, while payroll/tax derived rows should preserve existing workbook formulas or manual logic rather than require salary statement ingestion.
- 2026-05-11: Resolved salary writing behavior: matched Nordea net salary deposits may write `Full-time job (net)` when safe, while derived payroll/tax rows remain workbook-owned.
- 2026-05-11: Resolved income parent row behavior: `Income (net)` is formula/derived and should never be directly written by the updater.
- 2026-05-11: Resolved section total behavior: workbook section totals are derived rows and should never be direct write targets.
- 2026-05-11: Resolved salary multi-match behavior: sum deterministic salary-like deposits, but require review before writing if more than one appears in a reporting month.
- 2026-05-11: Resolved refund handling: same-month refunds net against deterministic matched categories, while unmatched/vague refunds remain review-only.
- 2026-05-11: Resolved cross-month refund handling: matched refunds affect the reporting month where they appear and do not retroactively adjust prior workbook periods.
- 2026-05-11: Resolved reimbursement scope: keep handling simple and aligned to the workbook; use `Expense claims` only when deterministically identified, without modelling offsets.
- 2026-05-11: Ended the `.agent` documentation grilling session and recorded its results/backlog in a separate planning block without changing `Active Tasks`.
- 2026-05-11: Created local PRD issue `.agent/issues/2026-05-11-prd-monthly-tracker-workbook-updater-next-slices.md` from the grilling session, labelled `ready-for-agent`.
- 2026-05-11: Split the PRD into seven local implementation issues and a kanban index under `.agent/issues/`.
- 2026-05-11: Created EOD summary in `docs/Daily_blogpost/2026-05-11.md`.
- 2026-05-12: Implemented `ISSUE-001` and `ISSUE-002` with TDD worker agents; full test suite passed with 47 tests.
- 2026-05-12: Implemented `ISSUE-003` refund/claim netting and `ISSUE-007` separate workbook cleanup workflow with TDD worker agents; full test suite passed with 57 tests.
- 2026-05-12: Created EOD summary in `docs/Daily_blogpost/2026-05-12.md`.
- 2026-05-13: Implemented `ISSUE-004` safe missing period/year planning and commit-to-copy structure creation with a TDD worker agent; full test suite passed with 65 tests.
- 2026-05-13: Confirmed `ISSUE-005` investment statement evidence remains HITL-blocked until a redacted statement sample and workbook mapping details are provided.
- 2026-05-13: Ended the CSV categorization grilling session after discovering the PDF was the wrong bank source; resolved Nordea CSV as the preferred bank cashflow source while keeping PDF fallback.
- 2026-05-13: Created Nordea CSV ingestion PRD and local issues `ISSUE-008` through `ISSUE-011`; real CSV files remain ignored and may be used only for local smoke validation.
- 2026-05-13: Implemented Nordea CSV ingestion slices `ISSUE-008` through `ISSUE-011` with sub-agents; CSV bank statements now parse merchant-rich transactions, route through `--statement-format`, expose parser metadata, add Mastercard liability/refund categorization, and document CSV-first local validation.
