# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Before exploring, read these

- **`.agent/System/domain_language.md`**: the project glossary (this repo's `CONTEXT.md` equivalent; no root `CONTEXT.md` exists yet).
- **`.agent/System/architecture.md`** and **`.agent/System/data_contracts.md`**: current shape and contracts.
- **`docs/adr/`**: read ADRs that touch the area you're about to work in.

If any of these files don't exist, **proceed silently**. `/domain-modeling` creates them lazily when terms or decisions actually get resolved.

## Layout

Single-context repo:

```
/
├── .agent/System/domain_language.md   ← glossary
├── docs/adr/                          ← NNNN-short-title.md
└── src/personal_wealth_tracker/
```

## Use the glossary's vocabulary

When your output names a domain concept (issue title, refactor proposal, hypothesis, test name), use the term as defined in the glossary. Don't drift to synonyms the glossary explicitly marks _Avoid_.

If the concept you need isn't in the glossary yet, either you're inventing language the project doesn't use (reconsider) or there's a real gap (note it for `/domain-modeling`).

## Flag ADR conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently overriding:

> _Contradicts ADR-0003 (blank means accept, atomic month commit), but worth reopening because…_
