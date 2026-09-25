# 0005: Hosted judgment deferred, local-only boundary kept

Status: accepted, 2026-09-25. Parent spec: GitHub issue #2. Recorded in issue #12.
Related: [0001](0001-per-row-authority.md), [0002](0002-local-two-model-consensus.md), [0003](0003-blank-means-accept-atomic-month-commit.md), [0004](0004-memory-learned-on-commit-with-provenance.md).

## Context

The trust-tier benchmark (`docs/superpowers/plans/2026-09-25-trust-tier-design.md`)
compared local Consensus with hosted judgment (TypeSafe Jev). Jev as a
verifier was slightly more precise, but it sends merchant text off the
machine, its confidence alone was not a usable authority, and the difference
sat inside gold-label noise. A later private rerun through the Suggester port (not the design
benchmark cited in ADR 0002) measured 0% invalid responses and the Consensus gate at 62 of 111 rows auto
with 90% precision. The project boundary so far: no financial data
leaves the machine.

## Decision

- The monthly flow is local only: two local voters under the Trust Policy
  (ADR 0002). No hosted model is called and no setting enables one.
- `outbound_redaction` stays in the package, tested but unused. It allowlists
  what could ever leave: a redacted merchant string, an amount band and the
  direction.
- The TypeSafe SDK stays behind the optional `hosted` extra; a default
  install does not pull it.
- A hosted Suggester adapter is designed, not built. Enabling one needs a new
  ADR, an explicit opt-in setting, the redaction module on every outbound
  row, and the provider's data-retention terms checked.

## Consequences

- The privacy boundary holds: merchant text, amounts and dates stay local.
- Precision is bounded by local models; the amount cap, never-auto list and
  memory provenance (ADRs 0001, 0004) bound the cost of shared wrong answers.
- Turning hosted judgment on later is one adapter plus one setting behind
  the Suggester port, not a pipeline change.
