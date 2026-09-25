# 0001: Per-row authority replaces cell blocking

Status: accepted, 2026-09-25. Parent spec: GitHub issue #2. Implemented in issue #5.

## Context

Whether a row could reach the Tracker Workbook was decided in three places:
categorizer confidence thresholds, the local LLM forcing every suggestion to
review, and the workbook planner blocking a whole cell when any source row
needed review. No single place said why a row was or was not trusted, and
no amount or category limit existed.

## Decision

Every `CategorizedTransaction` carries an `authority` (`auto` or `review`)
and a one-line `authority_reason`, decided by one pure Trust Policy
(`trust_policy.decide_authority(evidence, row, policy)`).

- Evidence: tier (categorization method), suggested category, confidence,
  model votes with source and confidence, agreement count, import provenance.
- Row facts: amount.
- Policy from `config/settings.yaml` `trust_policy`: `auto_max_amount`
  (1000), `min_agreement` (2), `never_auto_categories` (Rent, Parent B, Parent A, both
  insurances, three investment leaves, salary); `min_confidence` from
  `confidence_thresholds.auto_write`.

Only Trusted Statement Adapter rows can reach `auto`. Monthly Review
Decisions are `auto`. Above the cap or in the never-auto list is `review`
for every automatic tier, deterministic or model. The categorizer, the local
LLM step and the workbook planner read `authority` instead of deciding.

## Consequences

- Trust rules change in one module, tested as a table.
- Rows such as salary, rent and large credit-card payoffs now need a
  review decision every month unless the settings are changed.
- The workbook still blocks a cell whose source rows include a `review`
  row; the atomic month commit slice of issue #2 removes that later.
