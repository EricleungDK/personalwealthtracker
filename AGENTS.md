# AGENTS.md

Project-specific guidance for coding agents working in `PersonalWorthTracker`.

## Current State

- This repository is in the initial folder construction phase.
- Product requirements, framework choice, architecture, and implementation details are intentionally pending.
- Do not infer app behavior beyond the project name until project details are provided.

## Repository Discovery

Before implementing changes:

- Read this file.
- Read `.agent/README.md`.
- Read `.agent/Tasks/context.md`.
- Inspect project configuration files if they exist.
- Use `rg` or `rg --files` for codebase navigation.

## Project Structure

```text
PersonalWorthTracker/
├── AGENTS.md
├── README.md
├── .agent/
│   ├── README.md
│   ├── Tasks/
│   │   └── context.md
│   ├── System/
│   ├── SOP/
│   └── Reports/
├── docs/
├── src/
├── tests/
├── scripts/
├── config/
└── assets/
```

## Implementation Guidance

- Keep changes scoped and reversible.
- Prefer project conventions once they exist.
- Do not add dependencies, frameworks, services, telemetry, or generated assets without a clear requirement.
- Preserve user work and avoid unrelated edits.
- Update `.agent/Tasks/context.md` after significant decisions, implementation, or validation.

## Testing and Validation

- Add or update tests when changing behavior.
- Run the most relevant available checks before handoff.
- If no checks exist yet, state that clearly in the final handoff.

## Documentation

- Keep durable decisions in `.agent/Tasks/context.md` or the relevant `.agent/System/` document.
- Keep user-facing setup and usage notes in `README.md`.
- Avoid temporary process notes in user-facing documentation.
