# Decision Log

Last updated: 2026-09-27

The product decisions that are in force, grouped by topic. Each line gives the rule and, after the dash, why it exists. Bigger design decisions have ADRs in `docs/adr/`. Detailed history lives in git, the GitHub issues (#2-#20) and the historical `.agent/issues/` files.

## Product Boundary

- The product is a **Monthly Tracker Workbook Updater**, not a personal finance ledger. The workbook is the source of truth, and each run proposes category updates for one month (2026-05-11).
- The Reporting Month is explicit. `wealth-tracker monthly` infers it from the statement's row dates, and it is never taken from the run date (2026-05-11, #11).
- The tracker currency is DKK. Live FX is out of scope (2026-05-06).
- Nordea is the only bank source. CSV is preferred and PDF is the fallback. Generic multi-bank ingestion is a non-goal for the personal flow (2026-05-13).
- Real statements, workbooks, reports, backups, memory and `*.local.*` config never go into Git (2026-05-06).

## Workbook Authority

- Only evidence-backed leaf rows are written. Formula rows, section totals, and `Income (net)` are never written directly (2026-05-11).
- Matched Nordea net salary may write `Full-time job (net)`. Payroll and tax rows stay workbook-owned (2026-05-11).
- Internal transfers are excluded from income and expense unless deliberately mapped. Credit card payments settle a liability; they are not expenses (2026-05-11).
- Same-month deterministic refunds reduce the matched category. A refund in a later month counts in the month it appears, and earlier months are never reopened. Claims map to `Expense claims` (2026-05-11).
- Commits write to a copied workbook, never to the original (2026-05-06).
- Missing period and year columns copy the previous period's structure and formulas, clear copied manual values, and keep only configured `carry_forward_rows`. They appear in the dry run before commit (2026-05-11, ISSUE-004).
- Workbook label and currency cleanup is a separate one-off task, never part of a monthly run (2026-05-11).

## Per-Row Authority (current monthly flow)

- One Trust Policy (`trust_policy.py`) sets each row's authority to `auto` or `review`, replacing the review checks that used to be scattered. Automatic tiers have a 1000 DKK amount cap and a `never_auto_categories` list (2026-09-25, #5, ADR 0001).
- Two different local models must agree before a model suggestion gets `auto` authority: `gemma4:26b` and `gemma4:12b`, with `qwen3:14b` as fallback. A single model cannot vote twice (2026-09-25, #7, ADR 0002).
- The Exception Sheet (`Review Required`) lists only rows in review. A blank `manual_category` accepts the suggestion and `NONE` rejects it. A commit is atomic for the month: nothing is written while any row is still in review. `Audit` lists the auto rows (2026-09-25, #8, ADR 0003).
- There is one Exception Sheet per month. Its decisions carry forward, and `monthly` reads it only after the operator has saved it (SHA-256 fingerprint) (2026-09-26, #13, #20).
- Hosted judgment is deferred and the flow stays local only. `outbound_redaction` and the `hosted` extra are kept for a future opt-in adapter (2026-09-25, #12, ADR 0005).
- The Suggester prompt shows the raw merchant text. The normalised Merchant Identity is still the key for memory, aliases and validation (2026-09-26, #17).

## Category Registry And Leaves

- Workbook grouping rows (`Insurance`, `Living expenses`, `Services`) are Parent/Section Rows. Only Leaf Category Rows are valid targets (2026-05-20).
- Make YAML the durable category registry for parent/leaf semantics. `config/categories.yaml` is the registry, and each leaf has a `description` that the Suggester uses as a glossary (2026-05-20, #4).
- New leaves are requested through `new_parent_category`/`new_leaf_category`, never by overloading `manual_category` (2026-05-20).
- New leaves are saved to `categories.yaml` only after a successful commit, as a minimal text insert with a description. Dry runs and blocked runs leave the file unchanged (2026-09-26, #19).
- Missing leaf rows are inserted at the end of the parent's SUM section with formula-aware shifting and a before/after check that fails closed (2026-09-26, #16, ADR 0006).
- The generic `Subscriptions` leaf is replaced by per-service `<Service> subscription` leaf proposals, which always stay in review (2026-09-26, #14).

## Category Memory

- Category Memory may learn newly added categories only after leaf registry validation succeeds. Memory never points to a parent row, a derived row or a missing target (2026-05-20).
- Memory is learned when a commit succeeds, never in a dry run. Each mapping records its `provenance`. `human` comes from sheet decisions and Audit `corrected_category`. `auto` comes from consensus and is trusted only after two consistent committed months. `learn_to_memory=no` opts out, and `NONE` forgets the merchant's mapping (2026-09-25, #9, ADR 0004).
- Match order: human memory, then Guidance Alias (`config/guidance_aliases.local.yaml`), then trusted auto memory (2026-09-25, #10).
- Memory is keyed on the normalised Merchant Identity, with optional amount/date hints for recurring payments. It is stored in the ignored `data/category_memory/` (2026-05-11).
- `learn-category-memory` stays available as an escape hatch. It also updates `reviewed_policy.local.md`, which is given to the Suggester as guidance (2026-06-13).

## Proxy Split Transfers

- One Revolut top-up may pay for fixed family allocations (Dad, Mom). Base amounts are in source currency and multiplied by a configured conversion rate. Allocations are rounded to two decimals before the residual is calculated (2026-05-21).
- A split happens only when the transfer covers every allocation. An exact match leaves no residual. A larger transfer adds a Residual Review Line. The residual is never learned into memory (2026-05-21).
- `monthly_limit` is a configurable safety threshold. Candidates beyond it fail closed and go to review (2026-05-26).
- Concrete triggers and amounts belong in the ignored `config/rules.local.yaml` (2026-05-21).

## Local Models

- Ollama is called through its HTTP API, not the CLI. A provider failure never fails the run; the rows stay in review (2026-05-27).
- A Suggester can return only an existing leaf, `NONE`, or a subscription leaf proposal. Answers that name a leaf outside the list count as `NONE` (2026-09-25, #6, #14).

## Public Package

- The public shape is a local wealth-tracker agent: a Python CLI, a synthetic template workbook, synthetic examples, sample config and optional local models (2026-06-07, ISSUE-031 to ISSUE-040).
- Template customization is limited to known dimensions: categories, section labels, periods, currencies and profile paths. Arbitrary formulas and layouts are out of scope (2026-06-07).
- Unknown statement formats go through the Statement Import Assistant and stay untrusted until reviewed. A confirmed import can create a private Importer Profile that suggests Educated Import Guesses later (2026-06-07).
- `profiles/<name>.local.yaml` `profile_paths` supply path defaults for `monthly` and the per-month command. The order is: explicit flag, then profile, then built-in default. Profile paths are relative to the workspace that holds `profiles/` (2026-09-27).
- This repo incubates the package. The public/private split comes later (2026-06-07).

## Investments (planned, not built)

- Investment statements prove asset values, while bank statements prove cashflow. Neither source overrides the other outside its evidence type, and mismatches go to review (2026-05-11).
- Asset rows use the month-end market value and are updated only from explicit holding-level values. USD is converted to DKK at a user-maintained fixed rate, which is recorded in the report and audit, not in the workbook (2026-05-11).
- Crypto is out of scope until a dedicated valuation source exists (2026-05-11).

## Superseded

- "The LLM is review-only and never writes": superseded by two-model Consensus authority (ADR 0002).
- "Learning is a separate command from commit": superseded by learn-on-commit (ADR 0004).
- "One confirmed decision is enough for review-free categorization": still true for `human` memory. `auto` memory needs two committed months.
- "Every cell-level safety block is a review": superseded by atomic month commit (ADR 0003).
- Earlier model targets (`gemma4:e4b`, `gemma4:12b` as primary): superseded by the consensus pair above.
- "Register new leaves from the reviewed run": leaves now register on commit only (#19).
