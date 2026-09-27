# Reviewed Policy Memory Implementation Plan

Status: Implementation completed. Validated on 2026-09-05 as part of the full suite (204 passing tests). The checklist below preserves the original implementation plan. Later changes: Category Memory is now learned on commit with provenance and the reviewed policy lists `human` mappings only ([ADR 0004](../../adr/0004-memory-learned-on-commit-with-provenance.md)); the Local LLM prompt now includes raw merchant text (GitHub issue #17).

**Goal:** Generate an editable local reviewed policy from confirmed learned review decisions and include relevant policy context in Local LLM prompts.

**Architecture:** Category Memory remains the deterministic authority for exact reviewed merchant matches. A new local Markdown policy file under `data/category_memory/` is updated by the existing `learn-category-memory` workflow, preserving an editable manual guidance section. Local LLM prompt construction reads a small policy excerpt and includes it as review-only context without changing workbook write authority.

**Tech Stack:** Python 3.12, pytest, openpyxl, existing CLI and Category Memory modules.

---

### Task 1: Generate Reviewed Policy From Learned XLSX Decisions

**Files:**
- Modify: `src/personal_wealth_tracker/category_memory.py`
- Test: `tests/test_category_memory_cli.py`

- [ ] **Step 1: Write failing tests**

Add tests that `learn-category-memory` creates `reviewed_policy.local.md` from rows with `learn_to_memory=yes`, and preserves content under `## Manual Guidance` when regenerating.

- [ ] **Step 2: Run targeted tests and confirm RED**

Run: `uv run pytest -q tests/test_category_memory_cli.py::test_import_review_workbook_updates_reviewed_policy_from_learned_decisions tests/test_category_memory_cli.py::test_import_review_workbook_preserves_reviewed_policy_manual_guidance`

Expected: fail because the reviewed policy file is not created.

- [ ] **Step 3: Implement minimal generation**

Add constants for policy filename and section markers. After memory JSON is written, write a Markdown file with auto-generated entries from current mappings and preserve any existing manual section.

- [ ] **Step 4: Run targeted tests and confirm GREEN**

Run the same targeted test command. Expected: pass.

### Task 2: Include Reviewed Policy In Local LLM Prompts

**Files:**
- Modify: `src/personal_wealth_tracker/local_llm.py`
- Modify: `src/personal_wealth_tracker/pipeline.py`
- Test: `tests/test_local_llm.py`
- Test: `tests/test_pipeline_integration.py` if pipeline wiring needs coverage.

- [ ] **Step 1: Write failing tests**

Add a test that `build_local_llm_prompt(..., reviewed_policy=...)` includes a compact `reviewed_policy` field and excludes raw descriptions. Add a test or assertion that `apply_local_llm_suggestions` passes policy text read from the Category Memory directory.

- [ ] **Step 2: Run targeted tests and confirm RED**

Run: `uv run pytest -q tests/test_local_llm.py::test_prompt_includes_reviewed_policy_context`

Expected: fail because the prompt does not support reviewed policy context.

- [ ] **Step 3: Implement minimal prompt and pipeline wiring**

Load `data/category_memory/reviewed_policy.local.md` if present, extract the auto-generated examples plus manual guidance text, bound the prompt excerpt, and pass it into prompt construction.

- [ ] **Step 4: Run targeted tests and confirm GREEN**

Run: `uv run pytest -q tests/test_local_llm.py`.

### Task 3: Document And Verify

**Files:**
- Modify: `docs/monthly_workflow.md`
- Modify: `README.md`
- Modify: `.agent/System/data_contracts.md`
- Modify: `.agent/System/security_privacy.md`
- Modify: `.agent/Tasks/context.md`

- [ ] **Step 1: Update docs**

Document that `learn-category-memory` updates both deterministic Category Memory and editable reviewed policy guidance, and that the LLM uses policy context only for review suggestions.

- [ ] **Step 2: Run verification**

Run: `uv run pytest -q tests/test_category_memory_cli.py tests/test_local_llm.py tests/test_pipeline_integration.py tests/test_documentation.py`

Then run: `uv run pytest`

Expected: all tests pass.
