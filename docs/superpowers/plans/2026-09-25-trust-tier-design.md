# Design: one-command monthly import with calibrated trust

Status: superseded, 2026-09-25, by the spec
[2026-09-25-local-consensus-monthly-flow.md](../specs/2026-09-25-local-consensus-monthly-flow.md)
(config A, now implemented; see [docs/adr/](../../adr/)). Not built: config B,
`TypeSafeSuggester`, `CascadeSuggester` (hosted judgment deferred, ADR 0005). The
guidance file shipped as `config/guidance_aliases.local.yaml`. Benchmark numbers
below remain the reference. Originally superseded the "proposed design" section of the
2026-09 handoff. Written with the codebase-design vocabulary (module, interface,
seam, adapter).

## Goal

User drops Nordea CSV -> `wealth-tracker monthly` -> reviews only exceptions.
Two properties, in this order: auto-accepted rows are almost never wrong; the
exception list shrinks every month.

## Verdict on the two proposals

### User idea: LLM classifies, Jev judges confidence, harness re-asks LLM if low

Keep the instinct (calibrated confidence must gate automation; the local LLM's
self-reported confidence is not calibrated). Reject the shape, for four reasons.

1. Inverted roles. If a row may be sent to Jev at all, Jev should classify it,
   not grade someone else's answer. One `Choice` over the leaf list returns the
   full probability distribution plus calibrated `confidence` in one call. Using
   the LLM as primary and Jev as verifier does the work twice and keeps the
   weaker, uncalibrated answer as the primary.
2. The re-ask loop cannot add information. At temperature 0 the same prompt
   returns the same answer. If the prompt is changed to "the judge doubts you,
   here is its view", the LLM will mostly defer to the judge. Then the judge is
   deciding anyway, with extra latency and a cycle in the pipeline.
3. Cycles are the enemy of "simple to use". A bounded cascade (cheap answer ->
   one escalation with richer state -> human) is deterministic, testable, and
   explains itself in the audit sheet. A loop is none of these.
4. Privacy. `.agent/System/security_privacy.md:29` says no financial data to
   external APIs. Jev is hosted. This is a boundary change, needs an ADR and an
   explicit opt-in flag, and needs TypeSafe's data-retention terms checked.

### Handoff proposal

Mostly right. Changes:

- Reject the "Unreviewed" pseudo-leaf. It makes totals complete but wrong by
  category and creates a new cleanup step. Use atomic month commit instead
  (below).
- Reject cell-level blocking as the authority mechanism. Authority is decided
  per row, once, in one module (below). Cells derive from rows.
- Two local voters is a valid gate (98% on the 48% of rows where they agree),
  but the design must not hard-code it. The gate is a policy over evidence;
  which models supply the evidence is an adapter choice made after benchmark.

## Architecture

Today authority is smeared across three places: `categorizer.py` thresholds,
`local_llm.py:212` (always `review_required=True`), and
`workbook.py:807` (cell block). Concentrate it.

```
CSV -> import -> Categorizer ------------------------------> rows with Authority
                   |  memory / historical / recurring / rule   (in-process)
                   |  Suggester port  <- adapters: Ollama, TypeSafe, Fake
                   |  TrustPolicy (pure)  -> Authority {auto, review}
                 -> ReviewPlan (exceptions only) -> Commit (atomic) -> Memory.learn
```

### Module: TrustPolicy (new, pure, in-process)

Interface: `decide(evidence, row, policy) -> Authority`.

- `evidence`: source tier (memory-human, memory-auto, historical, rule,
  recurring, model), model votes `[ (category, confidence, source) ]`, and
  agreement count.
- `row`: amount, fixed-row flag, direction.
- `policy` (from `settings.yaml`): `auto_max_amount` (proposal: 1000 DKK),
  `min_confidence`, `min_agreement`, `never_auto_categories` (Rent, Mom, Dad,
  insurance, investments, salary).
- Output `Authority.auto` or `Authority.review` with a one-line reason.

Deletion test: delete it and the three smeared checks reappear. It earns its
keep. Every threshold decision becomes a table-driven unit test.

### Seam: Suggester port (replaces duck-typed Ollama client)

Interface: `suggest(rows, context) -> list[Suggestion]`.
`Suggestion = {transaction_id, category | None, confidence, alternatives,
evidence, source}`. `context` = leaf glossary, guidance aliases, up to N memory
examples nearest by normalized name.

Adapters (two or more, so the seam is real):

- `OllamaSuggester`: improved prompt from the benchmark (chat API, system msg,
  JSON schema with enum + NONE, glossary, `reason` before `category`,
  `think:false`, temp 0, `keep_alive`, cold-start timeout 180s, fallback that is
  installed).
- `TypeSafeSuggester` (opt-in): one `Choice` per row, criteria = leaf glossary +
  `NONE`, state = `{merchant, amount_band, direction, guidance}`. Sends merchant
  identity only unless `include_raw_description`. Many rows per request.
- `FakeSuggester` for tests. Returns scripted votes.
- `CascadeSuggester` composes two adapters: primary for every row, secondary
  only for rows the primary leaves uncertain, with the primary's top-3 and
  memory neighbours added to the secondary's context. One pass, no cycle.
  `ConsensusSuggester` (two primaries, agreement counted) is the same shape
  with `min_agreement=2`.

Which composition ships is a config choice, not code:

| config | primary | escalation | cloud | est. per row |
|---|---|---|---|---|
| A local-only | gemma4:26b + gemma4:12b consensus | none | no | ~4s |
| B hybrid | TypeSafe Choice | gemma4:26b on uncertain rows | yes, merchant only | sub-second most rows |

Pick after slice 3 benchmark. Do not build B until the privacy ADR is accepted.

### Review semantics

- Workbook review sheet lists only `Authority.review` rows, with the top
  suggestion prefilled and alternatives in a dropdown.
- Blank `manual_category` = accept prefilled suggestion. `NONE` = reject.
- Atomic month commit: `monthly` writes the workbook only when zero rows remain
  in review. Otherwise it writes the exception sheet and stops. Same command
  again after edits -> commit. The workbook never holds a partial month, which
  removes the silent under-count (handoff finding 4) without a fake leaf.

### Memory learning (no separate step)

On commit, every row is learned with provenance:

- `human`: from a filled review cell. Applies from next month, `Authority.auto`.
- `auto`: from consensus / high-confidence model. Applies as `auto` only after
  the same merchant+category is seen in 2 committed months; before that it is
  a model hint, not memory. Prevents a single model error from becoming
  permanent.
- `guidance.local.yaml`: hand-written aliases (canteen variants -> Lunch).
  Highest priority after human memory. Fixes the rows no model can know.

Audit sheet per month: every auto row with source, confidence, reason. Editing
an audit row reverses the memory entry.

### Taxonomy

Add `description:` to every leaf in `categories.yaml` (feeds the glossary and
the Choice criteria). Add leaves Restaurants, Entertainment, Subscriptions.

## Slices (TDD, in order)

1. `nordea_csv.py` accepts `YYYY/MM/DD` and `DD/MM/YYYY`.
2. `TrustPolicy` + `authority` on `CategorizedTransaction`; `_write_decision`
   reads `authority`, drops the cell-level `review_required` scan; `local_llm`
   stops forcing `review_required`. Tests: policy table, financial-authority
   invariant still holds.
3. Suggester port, `OllamaSuggester` with improved prompt, `FakeSuggester`.
   Benchmark test on a synthetic fixture (no private merchants in repo).
   Rerun the private benchmark with the harness; record numbers.
4. `ConsensusSuggester` + `CascadeSuggester`. Replay the benchmark jsonl files
   through them offline to pick thresholds (no model calls needed).
5. Exception-only review sheet, blank-means-accept, atomic commit.
6. Memory learn-on-commit with provenance and the 2-month rule; guidance file.
7. `wealth-tracker monthly`: newest CSV, infer month, run, print exceptions.
8. Only if privacy ADR accepted: `TypeSafeSuggester`, benchmark Jev on the
   111-row gold set, decide A vs B.

ADRs to record: per-row authority replaces cell blocking; blank means accept;
consensus/confidence as write authority with amount cap; hosted judgment opt-in
(if taken).

## Decisions only the user can make

1. Hosted Jev allowed for merchant name + amount band? If no, config A is final.
2. `auto_max_amount` and `never_auto_categories` list.
3. Atomic commit (recommended) vs partial write with pending marker.

## Benchmark result, 2026-09-25 (Jev vs local, 111 gold rows)

Jev `jev-1.13.0` received only the redacted merchant, amount band and
direction (`outbound_redaction.py`). Local numbers are from the earlier
Ollama run with the improved prompt. Gold labels are the prior agent's
judgment, so differences of 2-3 rows are inside label noise.

| model | accuracy | p50/row |
|---|---|---|
| jev (v2 instructions) | 82.0% (5 misses are MobilePay merchants the filter masked as person) | 0.23s |
| gemma4:26b | 85.6% | 2.5s |
| gemma4:12b | 78.4% | 1.5s |

Jev's own confidence is not a usable gate here: rows at conf >= 0.9 were
87% right. Agreement is:

| gate | auto rows | wrong |
|---|---|---|
| gemma4:26b + gemma4:12b (config A) | 66/111 | 4 |
| gemma4:26b + jev | 58/111 | 1 |
| gemma4:12b + jev | 55/111 | 1 |
| all three | 42/111 | 0 |

Conclusion: Jev alone cannot be the authority. Jev as second voter buys
about 3 fewer errors per 111 rows at the cost of 8 fewer auto rows and
sending merchant names off-machine. Local-only consensus stays the default;
the Suggester seam keeps a Jev verifier as a config switch if the exception
list is still too long after memory has grown. Harness:
`reports/_llm_bench/harness/bench_jev.py`, `ab_compare.py` (git-ignored).
