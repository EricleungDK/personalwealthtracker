# 0004: Category Memory learned on commit, with provenance

Status: accepted, 2026-09-25. Parent spec: GitHub issue #2. Implemented in issue #9.
Supersedes the earlier rule that Category Memory is learned only by a separate
import of `learn_to_memory=yes` rows and never from automatic matches.
Related: [0001](0001-per-row-authority.md), [0002](0002-local-two-model-consensus.md), [0003](0003-blank-means-accept-atomic-month-commit.md), [0005](0005-hosted-judgment-deferred.md).

## Context

Category Memory was learned only by the separate `learn-category-memory`
import, from rows marked `learn_to_memory=yes`. Blank-accepted Exception
Sheet rows (ADR 0003) were never learned, and consensus results (ADR 0002)
were never remembered, so the same merchant was re-asked every month. Letting
a single consensus answer become permanent memory would let one model error
repeat forever.

## Decision

- A successful Atomic Month Commit learns Category Memory for leaf categories
  that are not fixed rows; a dry run never does. Learning lives in the pipeline commit path.
- Each mapping carries `provenance`:
  - `human`: Exception Sheet decisions (blank accept or explicit leaf) and
    Audit sheet corrections. Categorises from the next month. `learn_to_memory`
    `no` opts a row out.
  - `auto`: consensus (`auto`-authority, voted) results, with the list of
    `committed_months`. Categorises only once the same merchant and category
    appear in two committed months; before that it is only a Suggester memory
    neighbour. A different category restarts the count. A merchant with any `human`
    mapping gets no `auto` mapping, and a `human` decision drops the
    merchant's `auto` mappings.
- Order: `human` memory, Guidance Alias, trusted `auto` memory, then the other
  deterministic tiers.
- The Audit sheet has a `corrected_category` column. A filled cell becomes a
  Monthly Review Decision on the next `--review-decisions` run; committing it
  replaces the merchant's mapping with a `human` one. `NONE` (from either
  sheet) removes the merchant's mappings without a recurring hint.
- Entries without `provenance` load as `human`. The reviewed policy file lists
  `human` mappings only. `learn-category-memory` stays as a manual escape hatch
  and writes `human` entries.

## Consequences

- No separate learn step in the monthly flow.
- A wrong consensus answer costs at most one more committed month of hints
  before an Audit correction, and never becomes memory on its own.
- Correcting a committed month means re-running commit for that month with
  the corrected workbook.
