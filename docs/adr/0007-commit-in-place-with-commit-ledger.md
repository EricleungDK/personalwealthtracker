# 0007: Commit in place, guarded by a backup and the Commit Ledger

Status: accepted, 2026-09-27.
Related: [0003](0003-blank-means-accept-atomic-month-commit.md), [0006](0006-formula-aware-leaf-row-insertion.md).

## Context

Commit mode always read the original Tracker Workbook and wrote a new
timestamped copy to `data/processed/`. The original never changed, so every
month started from it again: each copy held one month and ignored every earlier
commit. The tracker was never an incremental record.

## Decision

- An Atomic Month Commit updates the Tracker Workbook in place. A timestamped
  backup goes to `data/backups/` first; the updated workbook is saved as a
  sibling file and swapped over the tracker with `os.replace`, so a failed save
  never leaves a half-written tracker. The commit fails early if the tracker is
  open in Excel.
- The **Commit Ledger** (`data/commit_ledger.json`, ignored by Git) records the
  category amounts each committed month wrote, keyed by year-month and category
  label (row insertions do not break it).
- Re-committing a month (Audit correction, rerun) treats a cell that still
  holds its ledger amount as tool-owned: it is rewritten, or cleared when no
  statement row maps to that category any more. Any other value is the user's
  and stays in review as a manual value.
- `cleanup --commit` still writes a copy to `data/processed/`.

## Consequences

- Committed months accumulate in one workbook; opening `Net Worth Tracker.xlsx`
  shows the full history.
- Recovery from a bad commit is restoring the latest file in `data/backups/`.
- Deleting the Commit Ledger makes earlier commits look like manual values, so
  re-committing those months sends their rows to review; new months are
  unaffected.
