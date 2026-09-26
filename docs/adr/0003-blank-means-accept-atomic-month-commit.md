# 0003: Blank means accept, atomic month commit

Status: accepted, 2026-09-25. Parent spec: GitHub issue #2. Implemented in issue #8.
Related: [0001](0001-per-row-authority.md), [0002](0002-local-two-model-consensus.md), [0004](0004-memory-learned-on-commit-with-provenance.md), [0005](0005-hosted-judgment-deferred.md).

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
  dropdown of the suggestion, Suggester alternatives and voted categories
  first, then `NONE`, then every leaf (issue #18: per-row list in the hidden
  `Decision Options` sheet, so no inline-list length cap).
- Blank `manual_category` accepts `suggested_category`. `NONE` rejects it:
  the row becomes a Monthly Review Decision with no category and is written
  nowhere. Any other value is an explicit category. `manual_category` itself
  is written empty; the suggestion is prefilled in `suggested_category`. A
  blank row without a suggestion stays in review.
- Commit mode writes the backup and copied Tracker Workbook only when zero
  rows remain in review. New leaves from the sheet reach
  `config/categories.yaml` in the same step, never earlier (issue #19). Otherwise it writes the Exception Sheet, reports
  `Workbook not written: N row(s) in review.` and stops. Re-running with the
  filled sheet as `--review-decisions` commits.
- `monthly` reads the Exception Sheet as decisions only after the operator
  saved it (issue #13). Each time the tool writes the sheet it records its
  SHA-256 and mtime in `review_required_<year>_<mon>.xlsx.written`; while
  both still match, the sheet counts as unreviewed, is not read, and the
  next action is `Exception sheet not reviewed yet: <path>`. Exit code stays
  0. The explicit `--review-decisions` path always reads the given file.
- The sheet is operator-first (issue #18): `date`, `description`, `amount`,
  `suggested_category` (`suggested_parent_category` only when a row proposes
  a new leaf), `manual_category` (header note: blank accepts, no suggestion
  needs a category or `NONE`), `reason` (method appended), `confidence`, the
  optional inputs, a `blocked` note filled only for a `review` workbook
  update, split columns only when split rows exist, and a hidden
  `transaction_id`. Rows without a suggestion sort first, then by date.
  `Category Options` and `Run Metadata` are hidden. Decisions are read by
  header name, so earlier layouts still load.
- Cell-level blocking is removed. There is no "Unreviewed" pseudo-leaf.
- The `Audit` sheet lists every `auto` row not in review with source, votes
  and reason.

## Consequences

- A mostly-correct Exception Sheet needs no typing, but must be saved:
  re-running `monthly` without opening it never accepts unseen suggestions.
- The Tracker Workbook never holds a partial month.
- Never-auto rows (salary, rent) block the commit every month until decided;
  blank accepts them in one pass.
- Rows whose workbook cell is blocked (manual value, missing row, several
  salary deposits) also block the commit; they need a different category,
  `NONE`, or a workbook fix.
