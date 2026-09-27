# 0002: Local two-model consensus with amount cap as write authority

Status: accepted and implemented, 2026-09-25. Parent spec: GitHub issue #2. Implemented in issues #6, #7; amended by #14.
Related: [0001](0001-per-row-authority.md), [0003](0003-blank-means-accept-atomic-month-commit.md), [0004](0004-memory-learned-on-commit-with-provenance.md), [0005](0005-hosted-judgment-deferred.md).

## Context

Local model suggestions were always `review`, so every unmatched row needed a
manual decision each month. The trust-tier benchmark
(`docs/superpowers/plans/2026-09-25-trust-tier-design.md`) measured
`gemma4:26b` + `gemma4:12b` agreement at 66 of 111 rows auto with 4 wrong,
while a single model's self-reported confidence was not a usable authority.
Hosted judgment (Jev) scored slightly better but sends merchant text off the
machine.

## Decision

Model suggestions reach the Tracker Workbook only through Consensus under the
Trust Policy (ADR 0001).

- `ConsensusSuggester` asks two local Suggesters per row, primary first; each
  answering model is one `Vote`. Off-leaf answers count as NONE; failed voters
  cast no vote.
- `auto` needs `trust_policy.min_agreement` (2) distinct models on the same
  leaf, amount within `auto_max_amount` (1000 DKK), and a leaf outside
  `never_auto_categories`.
- Otherwise the row is `review`, suggesting the primary model's leaf (else
  the second's) with the other answers as alternatives.
- A voter may instead propose a new `<Service> subscription` leaf under
  Services (issue #14). An existing leaf beats a proposal; proposals with the
  same normalised name agree, but a proposal is always `review` and becomes a
  new leaf only when the operator accepts it on the Exception Sheet.
- Defaults: `model` `gemma4:26b`, `second_model` `gemma4:12b`,
  `fallback_model` `qwen3:14b`. The fallback is a different model so a
  missing voter cannot be replaced by the other voter's model; agreement
  counts distinct sources as a second guard.

## Consequences

- Recurring low-value merchants stop needing review; large sums and
  sensitive categories always need a human.
- Every model row costs two local calls (≈4 s); nothing leaves the machine.
- A wrong answer both models share can be written; the cap bounds its size
  and memory learning with provenance limits its reach.
