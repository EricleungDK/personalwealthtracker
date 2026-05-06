# Agent Memory

This directory stores durable context for agents working on `PersonalWorthTracker`.

## Layout

```text
.agent/
├── README.md
├── Tasks/
│   └── context.md
├── System/
├── SOP/
└── Reports/
```

## Usage

- Treat `Tasks/context.md` as the central project state file.
- Store architecture, schema, API, and integration references in `System/`.
- Store repeatable workflows in `SOP/`.
- Store research, debugging, validation, and handoff reports in `Reports/`.
- Keep this memory current when major project decisions or task status changes.
