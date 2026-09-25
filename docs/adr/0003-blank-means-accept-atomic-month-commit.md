# 0003: Blank means accept, atomic month commit

Status: accepted, 2026-09-25. Parent spec: GitHub issue #2. Implemented in issue #8.

## Context

The review workbook listed rows without a decision column default, so every
row needed typing. Commit mode wrote every writable cell even while other
rows were still in review, so a month could land partially and a category
could be silently under-counted. A cell with any `review` source row was
blocked on its own (ADR 0001 left this in place).

## Decision

- The `Review Required` sheet is the Exception Sheet: only rows in review
  (`review` authority, or the source of a workbook update planned as
  `review`), with `suggested_category` shown and a `manual_category`
  dropdown of the suggestion, vote alternatives and `NONE`.
- Blank `manual_category` accepts `suggested_category`. `NONE` rejects it:
  the row becomes a Monthly Review Decision with no category and is written
  nowhere. Any other value is an explicit category. `manual_category` itself
  is written empty; the suggestion is prefilled in `suggested_category`. A
  blank row without a suggestion stays in review.
- Commit mode writes the backup and copied Tracker Workbook only when zero
  rows remain in review. Otherwise it writes the Exception Sheet, reports
  `Workbook not written: N row(s) in review.` and stops. Re-running with the
  filled sheet as `--review-decisions` commits.
- Cell-level blocking is removed. There is no "Unreviewed" pseudo-leaf.
- The `Audit` sheet lists every `auto` row with source, votes and reason.

## Consequences

- A mostly-correct Exception Sheet needs no typing.
- The Tracker Workbook never holds a partial month.
- Never-auto rows (salary, rent) block the commit every month until decided;
  blank accepts them in one pass.
- Rows whose workbook cell is blocked (manual value, missing row, several
  salary deposits) also block the commit; they need a different category,
  `NONE`, or a workbook fix.
