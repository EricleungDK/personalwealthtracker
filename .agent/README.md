# Agent Memory

This directory stores durable context for agents working on `PersonalWorthTracker`.

## Layout

```text
.agent/
├── README.md
├── Tasks/
│   └── context.md
├── System/
└── issues/
```

## Usage

- Treat `Tasks/context.md` as the central project state file.
- Store architecture, schema, API, and integration references in `System/`.
- Store local PRDs, implementation slices, and kanban state in `issues/`.
- Create `SOP/` or `Reports/` only when a durable workflow or report archive is actually needed.
- Keep this memory current when major project decisions or task status changes.
