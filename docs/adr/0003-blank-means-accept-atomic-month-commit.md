# 0003: Blank means accept, atomic month commit

Status: accepted and implemented, 2026-09-25. Parent spec: GitHub issue #2. Implemented in issue #8; amended by #13, #18, #19, #20.
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
- `monthly` blank-accepts on the Exception Sheet only after the operator
  saved it (issue #13). Each time the tool writes the sheet it records its
  SHA-256 and mtime in `review_required_<year>_<mon>.xlsx.written`; while
  both still match, the sheet counts as unreviewed, only its filled cells
  are read (issue #20, below), and the next action is
  `Exception sheet not reviewed yet: <path>`. Exit code stays
  0. The explicit `--review-decisions` path always reads the given file.
- One Exception Sheet per month (issue #20). Every `monthly` run rewrites
  `review_required_<year>_<mon>.xlsx` in place and carries forward every
  decision it read, matched by `transaction_id`: prefilled `manual_category`
  (a blank accept is written as the accepted category), `new_parent_category`
  / `new_leaf_category`, `learn_to_memory` `no`, and Audit
  `corrected_category`. Decided rows show no `suggested_category` (except
  an accepted proposal, see below), so clearing a prefilled cell reopens
  the row instead of re-accepting it. Rows needing a decision come first, then decided
  rows by date; rows newly in review are added. Dropdowns are regenerated on
  every write, since Excel drops openpyxl's list extensions on save.
  `monthly` writes no `_after_decisions.xlsx`; the per-month
  `--review-decisions` path keeps writing it.
- Guard interaction: the rewrite gets a fresh `.written` fingerprint. An
  unsaved sheet is still read, but only its filled cells count (no blank
  accept). Carried decisions are filled cells, so they keep applying
  without another save; a blank row, including one added or newly suggested
  by the rewrite, is accepted only after the operator saves. A carried
  accepted Subscription Leaf Proposal is written as `new_*` cells equal to
  the shown proposal, and the loader reads that match as accepting it.
- Fail safe: a sheet that cannot be read (corrupt), cannot be rewritten
  (open in Excel) or holds invalid decisions stops the run before any
  commit or output, so it is never overwritten or left stale.
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
- The operator fills one file for the whole month; each re-run shows the
  remaining rows on top and never replays or loses earlier decisions.
- A committed month's sheet still carries its decisions, so re-running
  `monthly` without changes commits the same month again (new backup and
  copy), as an all-`auto` month already did.
- The Tracker Workbook never holds a partial month.
- Never-auto rows (salary, rent) block the commit every month until decided;
  blank accepts them in one pass.
- Rows whose workbook cell is blocked (manual value, missing row, several
  salary deposits) also block the commit; they need a different category,
  `NONE`, or a workbook fix.
