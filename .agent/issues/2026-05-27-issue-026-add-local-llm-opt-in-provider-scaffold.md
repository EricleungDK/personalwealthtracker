---
type: issue
id: ISSUE-026
title: Add Local LLM Opt-In Provider Scaffold
status: done
slice_type: AFK
labels:
  - done
parent: 2026-05-27-prd-local-gemma-review-suggestions.md
blocked_by: []
created: 2026-05-27
---

# Add Local LLM Opt-In Provider Scaffold

## Parent

[PRD: Local Gemma Review Suggestions](./2026-05-27-prd-local-gemma-review-suggestions.md)

## What To Build

Add the first end-to-end Local LLM Mode path without producing category suggestions yet. A monthly run should accept an explicit local-LLM opt-in, load local provider settings for Ollama/Gemma, detect provider unavailability through a mockable local HTTP integration, and continue the run with ordinary review output plus a visible warning when the provider is unavailable.

## Acceptance Criteria

- [x] Local LLM Mode is disabled by default and does not run merely because Ollama is installed.
- [x] The monthly CLI exposes an explicit opt-in for local model suggestions.
- [x] Config supports local Ollama provider settings including endpoint, default model, fallback model, timeout, and raw-description prompt mode disabled by default.
- [x] The initial documented model defaults are `gemma4:e4b` and fallback `gemma4:e2b`.
- [x] Provider calls use Ollama's local HTTP API, not `ollama run`.
- [x] Provider availability checks are mockable in tests and do not require a real Ollama installation.
- [x] If Ollama is unavailable, the monthly run still completes with ordinary deterministic/unmatched review output.
- [x] Provider unavailability appears as a report or audit warning.
- [x] Tests cover disabled mode, explicit opt-in, config loading, provider unavailable fallback, and no accidental model call when disabled.

## Blocked By

None - can start immediately.
