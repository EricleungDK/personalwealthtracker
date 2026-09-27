# Spec: one-command monthly flow with local consensus authority (config A)

Status: implemented. Tracked as GitHub issue #2, built in issues #3-#20, merged in PR #15.
Later issues changed details below: per-service `<Service> subscription` leaves
replace the generic Subscriptions leaf (#14), the prompt sends raw merchant text
(#17), one Exception Sheet per month carries decisions forward (#20). Hosted
judgment stays deferred ([ADR 0005](../../adr/0005-hosted-judgment-deferred.md)).
Current decisions: [docs/adr/](../../adr/).

Decided 2026-09-25 after the trust-tier design discussion and the Jev vs local
benchmark (`docs/superpowers/plans/2026-09-25-trust-tier-design.md`).

## Problem Statement

Every month I download the Nordea CSV and then run a seven-step loop: dry-run,
open the review workbook, fill categories, dry-run again with decisions, learn
memory, dry-run again, commit. Around 70% of rows land in review because the
learning state is empty and recurring merchants are re-asked every month. The
local model's suggestions always require my confirmation, one unsure row
blocks a whole category cell, and a commit made before review silently
under-counts a category. The date format in newer exports is not even parsed.
I want to categorise a month in minutes, trust what the tool auto-accepts, and
look only at the rows it genuinely cannot decide.

## Solution

One command, `wealth-tracker monthly`, takes the newest CSV, categorises every
row through deterministic tiers first and a local two-model consensus second,
stamps each row with an authority (`auto` or `review`), and either commits the
month to a copied Tracker Workbook when nothing is left to review, or writes an
exception sheet listing only the undecided rows. Blank in the exception sheet
means "accept the prefilled suggestion". Re-running the same command after
filling the sheet commits. Every committed row teaches Category Memory with
provenance, so the exception list shrinks month over month. Nothing leaves the
machine.

## User Stories

1. As the operator, I want one command that finds the newest statement export, so that I do not type paths or months.
2. As the operator, I want the month inferred from the statement dates, so that I cannot pick the wrong period column.
3. As the operator, I want both `YYYY/MM/DD` and `DD/MM/YYYY` Nordea exports parsed, so that a bank format change does not break the month.
4. As the operator, I want recurring merchants (Rejsekort, DonkeyRepublic, Voi, canteen, subscriptions) categorised automatically, so that I never review them again.
5. As the operator, I want a hand-written guidance alias file for merchants whose names vary (canteen variants → Lunch), so that personal context no model can know is captured once.
6. As the operator, I want the local model's suggestions to be auto-accepted only when two local models agree, so that automation is backed by the measured 94-98% consensus precision rather than a self-reported confidence.
7. As the operator, I want any row above an amount cap (default 1000 DKK) to go to review regardless of model agreement, so that a wrong guess can never move a large sum silently.
8. As the operator, I want a never-auto category list (Rent, Mom, Dad, insurances, investments, salary) so that fixed and sensitive categories are always confirmed by me.
9. As the operator, I want rows the models disagree on, answer NONE for, or that match no leaf to be listed as exceptions with the best suggestion prefilled and alternatives offered, so that review is a glance and a keystroke.
10. As the operator, I want blank in the exception sheet to mean "accept the suggestion", so that a mostly-correct sheet needs no typing.
11. As the operator, I want an explicit `NONE` in the exception sheet to mean "reject; leave uncategorised", so that I can refuse a suggestion without inventing a category.
12. As the operator, I want the Tracker Workbook written only when zero rows remain in review, so that a month is never partially written and no category is under-counted.
13. As the operator, I want a clear terminal summary after each run (auto rows, review rows, pending amount, next action), so that I know whether I am done.
14. As the operator, I want every auto-accepted row recorded in an audit sheet with its source, votes and reason, so that I can spot-check automation.
15. As the operator, I want to correct an audit row and have the correction reverse the learned memory entry, so that one mistake does not repeat.
16. As the operator, I want human decisions learned into Category Memory immediately with provenance `human`, so that next month the same merchant is auto.
17. As the operator, I want model-consensus results learned with provenance `auto` but only trusted as memory after two consistent committed months, so that a single model error cannot become permanent.
18. As the operator, I want the separate "learn category memory" step to disappear, so that learning is a side effect of committing.
19. As the operator, I want the local model prompt to use a structured JSON schema with the leaf list and a per-category glossary, so that invalid responses drop from 12-46% to about 0%.
20. As the operator, I want the default local model to be the best-measured one (gemma4:26b) with gemma4:12b as the second voter, and an installed fallback, so that the configuration works out of the box on my machine.
21. As the operator, I want the model kept warm and a cold-start timeout that covers a 60+ second first load, so that the first row of the month does not fail.
22. As the operator, I want a `description:` per leaf in the categories file, so that the glossary the models see is mine, not hard-coded.
23. As the operator, I want Restaurants, Entertainment and Subscriptions leaves available, so that the models stop answering categories that do not exist.
24. As the operator, I want a run with no local model available to still complete deterministically and list everything else as exceptions, so that the flow degrades instead of failing.
25. As the operator, I want a dry-run flag on the monthly command, so that I can preview the exception sheet and audit without touching memory or workbook.
26. As the operator, I want the original workbook untouched and a backup taken before the copied workbook is written, so that the existing safety guarantees hold.
27. As the operator, I want the review-only financial authority rule for untrusted imports preserved, so that Statement Import Assistant output never becomes auto.
28. As the operator, I want the trust policy thresholds in the settings file, so that I can change the cap or the never-auto list without code.
29. As the operator, I want the hosted judgment path (TypeSafe Jev) to remain off and its redaction module kept, so that the privacy boundary holds today and the option costs one config line later.
30. As a future maintainer, I want the authority decision in one module and cell writes derived from row authority, so that there is one place to change trust rules.
31. As a future maintainer, I want the model provider behind a single port with a fake adapter, so that the whole flow is testable without Ollama.
32. As a future maintainer, I want the new decisions recorded as ADRs, so that the change from review-only authority is traceable.

## Implementation Decisions

- **Config A, local only.** Two local voters, gemma4:26b primary and gemma4:12b second. No hosted model in the monthly flow. Benchmark: consensus 66/111 auto rows with 4 wrong; Jev as verifier 58 with 1 wrong; Jev alone not a usable authority (conf ≥0.9 only 87% right). Difference is inside gold-label noise and shrinks as memory grows.
- **Deterministic first, unchanged order**: Category Memory → historical → recurring → rule → Suggester → TrustPolicy. Guidance aliases sit directly after human memory.
- **TrustPolicy** is a new pure module. Input: evidence (tier, model votes with source and confidence, agreement count), row facts (amount, fixed-row flag, direction, category type), policy from settings (`auto_max_amount` default 1000 DKK, `min_agreement` default 2, `never_auto_categories` default Rent, Mom, Dad, both insurances, the three investment leaves, salary). Output: `Authority.auto` or `Authority.review` plus a one-line reason. `CategorizedTransaction` gains an `authority` field. The three existing scattered checks (categorizer thresholds, LLM always-review, workbook cell scan) are replaced by reading `authority`.
- **Suggester port** replaces the duck-typed Ollama client. `suggest(rows, context) -> suggestions` where a suggestion carries category or NONE, confidence, alternatives, evidence text and source. Context carries the leaf glossary, guidance aliases and up to N memory neighbours by normalised merchant identity. Adapters: Ollama (improved prompt: chat endpoint, system message, JSON schema with enum leaves + NONE, `reason` before `category`, thinking off, temperature 0, keep-alive, 180 s cold-start timeout, installed fallback), Fake (scripted votes for tests), Consensus (two adapters, agreement counted). Cascade and TypeSafe adapters are designed but not built.
- **Exception-only review sheet**: only `review` rows, suggestion prefilled, alternatives as a dropdown, blank = accept, `NONE` = reject. Replaces the whole-month review workbook.
- **Atomic month commit**: the monthly command writes the copied workbook only when zero rows remain in review. Otherwise it writes the exception sheet and stops with a summary. Same command re-run after edits commits. The workbook never holds a partial month. Cell-level blocking is removed. No "Unreviewed" pseudo-leaf.
- **Memory learn-on-commit** with provenance `human` (applies next month) or `auto` (applies as memory only after the same merchant+category is seen in two committed months; before that it is a hint to the Suggester context). Audit sheet edits reverse memory. The standalone learn command remains only as a manual escape hatch.
- **Guidance alias file** (private, git-ignored, next to rules.local.yaml): merchant pattern → leaf. Highest priority after human memory.
- **Taxonomy**: add `description:` per leaf; add Restaurants, Entertainment, Subscriptions leaves (Restaurants as a Living-expenses leaf; dining is not folded into Food & Drinks).
- **Trusted Statement Adapter fix**: Nordea CSV date parsing accepts both formats.
- **Monthly command**: newest CSV in the raw statements folder, month inferred from row dates, runs categorise → suggest → policy → exception sheet or commit, prints summary; `--dry-run` skips memory and workbook writes.
- **Financial authority invariant kept**: Untrusted Imported Transactions and Educated Import Guesses stay `review`; only Trusted Statement Adapter rows can reach `auto`.
- **Privacy**: `outbound_redaction` module stays in the package (tested, unused by the flow) and the TypeSafe SDK stays an optional extra. Security doc gains a line that hosted judgment is opt-in only and not enabled.
- **ADRs** (new `docs/adr/`): 0001 per-row authority replaces cell blocking; 0002 local two-model consensus with amount cap as write authority; 0003 blank-means-accept and atomic month commit; 0004 hosted judgment deferred, local-only boundary kept. (As built: 0004 is memory learned on commit with provenance, 0005 hosted judgment deferred, 0006 formula-aware leaf row insertion.)
- **Glossary additions** for domain_language.md: Authority, Trust Policy, Suggester, Consensus, Exception Sheet, Guidance Alias, Atomic Month Commit.
- Dead code `pipeline._validate_target_period` removed after confirming the trusted import covers period checks.

## Testing Decisions

- Tests describe observable behaviour through the highest seam: `run_pipeline` (and the CLI `monthly` command) with a Fake Suggester injected and synthetic fixtures. Prior art: the pipeline integration and pipeline safety tests, the CLI tests, the financial authority test.
- Second seam: TrustPolicy is exercised directly as a pure function with a table of (evidence, row, policy) → authority. It is a deep module whose interface is the test surface.
- The Ollama adapter is tested with a stubbed HTTP transport for request shape and response parsing, as the existing local LLM tests do; no live model in the suite.
- No real merchants, people or statements in fixtures; the security doc's synthetic-fixture rule applies.
- Old tests that assert cell-level review blocking or always-review LLM rows are replaced, not layered.
- The private benchmark harness stays git-ignored and is rerun manually after the prompt port to confirm invalid rate ≈0% and consensus precision.
- TDD per slice: date fix → TrustPolicy → Suggester port + Ollama prompt → Consensus → exception sheet + atomic commit → memory learn-on-commit + guidance → monthly command → ADRs and docs.

## Out of Scope

- TypeSafe / hosted judgment in the pipeline (redaction module and SDK extra remain available).
- Cascade adapter, embedding kNN few-shot, bigger models.
- Bank fetch automation, PSD2 aggregators, Windows Task Scheduler or folder watch.
- Investment statement evidence (issues 005/006 remain blocked).
- Changing the Tracker Workbook layout or formulas.

## Further Notes

- Benchmark evidence lives in `docs/superpowers/plans/2026-09-25-trust-tier-design.md` (numbers) and the git-ignored `reports/_llm_bench/` (harness, per-row results, `ab_summary.md`).
- Rejected ideas and why: LLM-then-Jev-then-re-ask loop (re-ask adds no information at temperature 0, induces deference, adds a cycle); Jev as primary (not calibrated enough on this domain, 82% accuracy through the redaction filter); "Unreviewed" bucket (complete but wrong totals plus a cleanup step).
- Runtime expectation: two voters ≈4 s per unmatched row; ~100 rows ≈ 7 min cold month, far fewer rows once memory is warm.
- Gold labels for the benchmark were the prior agent's judgment, so the operator's own review decisions should replace them as the eval set after the first real month.
