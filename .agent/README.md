# Agent Memory

This directory stores durable context for agents working on `personalwealthtracker`.

## Layout

```text
.agent/
├── README.md
├── Tasks/
│   └── context.md   # short state snapshot + doc map
├── System/          # decisions log, requirements, architecture, data contracts, domain language, security
└── issues/          # historical local issues 001-040 (read-only)
```

## Usage

- `Tasks/context.md`: short current-state snapshot and doc map; keep it under ~50 lines.
- `System/decisions.md`: current decisions by topic; mark superseded ones instead of appending history.
- Store architecture, schema, API, and integration references in `System/`.
- Track new work in GitHub Issues (`EricleungDK/personalwealthtracker`, see `docs/agents/issue-tracker.md`); `issues/` is kept for history only.
- ADRs live in `docs/adr/`; specs in `docs/superpowers/specs/`.
- Create `SOP/` or `Reports/` only when a durable workflow or report archive is actually needed.
- Keep this memory current when major project decisions or task status changes.
