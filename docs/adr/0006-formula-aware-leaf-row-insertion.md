# 0006: Formula-aware leaf row insertion, fail closed

Status: accepted, 2026-09-26. Implemented in issue #16.
Related: [0003](0003-blank-means-accept-atomic-month-commit.md).

## Context

A missing registered leaf was placed after its highest config sibling row.
The real workbook groups rows differently from `config/categories.yaml`
(for example `Traveling` sits under `Others`), so the placement crossed the
next section and every run blocked the rows in review. openpyxl's
`insert_rows` also moves cells only: formulas such as
`Recurring payments = D55+D64+D72+D76`, section SUMs, `Cashflow` and
`Total net worth` would keep pointing at the old rows, and only one month's
parent SUM was expanded.

## Decision

- Section extent is the parent row's `=SUM(Xa:Xb)` in the target month
  column; the new leaf goes at `b + 1`. Without a parent formula the section
  ends at the next parent/derived row. Any other parent formula shape, or a
  SUM that reaches past the next section, stays `review`.
- `row_insertion.insert_row_with_formulas` rewrites every row reference at or
  below the new row with openpyxl's formula tokenizer (relative/absolute,
  ranges, whole rows, other sheets pointing at this sheet), grows the parent
  SUM in every column (keeping `$` markers), and shifts merged cells, conditional formats, data validations, defined names,
  print area and row dimensions.
- Safety check, before anything is saved: every pre-existing cell must be at
  its shifted position with its expected formula, and every formula the small
  evaluator supports (numbers, references, `SUM`, `+ - * / ^`) must give the
  same value with the new row empty. Unsupported formulas rely on the
  structural check. Excel tables, array formulas and `INDIRECT`/`OFFSET`
  block insertion, as does any parent-row formula that is not a same-column
  SUM ending right above the new row. Grown parent totals must be evaluable.
- Planning applies each structure change to the in-memory workbook in order,
  the same order commit replays them, so several new leaves in one run and
  all value updates use final row numbers. A failed check turns that change
  into `review` with the reason; commit raises if a replayed check fails.

## Consequences

- New leaves in the normal case need no manual workbook edit.
- Formulas outside the evaluator's subset (for example `IFERROR` growth rows)
  are protected by the structural check only.
- Workbooks with tables or position-dependent functions keep needing a manual
  row insert.
