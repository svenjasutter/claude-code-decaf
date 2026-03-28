# Tasks: US1 Automated Test Coverage

**Input**: Design documents from `/specs/002-us1-tests/`
**Prerequisites**: plan.md (required), spec.md (required)
**Depends on**: `/specs/001-simple-claude-code/` (US1 implementation complete)

**Organization**: Tasks are grouped by test layer (fixtures, unit, integration).

## Format: `[ID] [P?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

---

## Phase 1: Shared Fixtures

**Purpose**: Shared test infrastructure used by all test files

- [x] T001 [P] Create `tests/conftest.py` with shared pytest-asyncio fixtures: `make_text_response(text)` builds a mock ProviderResponse with a text-only content block; `make_tool_use_response(tool_name, tool_input, tool_use_id)` builds a mock ProviderResponse with a tool_use block; `make_thinking_response(thinking, text)` builds a mock ProviderResponse with thinking + text; `event_collector(event_bus)` subscribes to all event types and captures events in a list; `_make_block` helper for creating MagicMock content blocks with correct attribute handling
- [x] T002 [P] Set `asyncio_mode = "auto"` in `pyproject.toml` `[tool.pytest.ini_options]`; create `tests/__init__.py`

**Checkpoint**: Fixtures importable and pytest configured.

---

## Phase 2: Unit Tests

**Purpose**: Test each module in isolation with mocked dependencies

- [x] T003 [P] Unit tests for EventBus in `tests/test_events.py`: subscribe and emit, multiple subscribers on same event type, subscriber exception does not crash other subscribers or caller, different event types are isolated, emitting with no subscribers does not raise (6 tests)
- [x] T004 [P] Unit tests for AnthropicProvider in `tests/test_provider.py`: mock `AsyncAnthropic.messages.create`; verify `send()` passes correct params (model, max_tokens, thinking config, system, tools, messages); test `_map_response` for text-only, thinking+text, and tool_use responses; verify TokenUsage populated; verify thinking token estimation; verify API exceptions propagate (7 tests)
- [x] T005 [P] Unit tests for Agent class in `tests/test_agent.py`: mock `provider.send()` and tool functions; test text-only response (AC-1, AC-3); single/multiple/chained tool calls (AC-2); unknown tool error; tool execution failure; approval denied/approved; tool timeout; output truncation; API error with history preservation; event ordering; conversation history across calls; TC-002 raw_content compliance (14 tests)
- [x] T006 [P] Unit tests for tool loader in `tests/test_loader.py`: verify `load_tools()` discovers all Python tools and CLI-only tool (prettier); tool_functions are async callables; approval_required from config.yaml; skill_md_contents populated; directories without SKILL.md ignored (6 tests)
- [x] T007 [P] Unit tests for main.py helpers in `tests/test_main.py`: `build_system_prompt()` with all parts and with empty memory; `load_memory_files()` with missing files, with CLAUDE.md, and with 200-line MEMORY.md truncation; API key validation (6 tests)

**Checkpoint**: All unit tests pass. `pytest tests/test_events.py tests/test_provider.py tests/test_agent.py tests/test_loader.py tests/test_main.py -v` shows 39 passed.

---

## Phase 3: Integration Tests

**Purpose**: Test the full agent loop with real tools and real EventBus, mocking only the provider

- [x] T008 Integration tests for agent loop in `tests/test_integration_agent.py`: mock only `provider.send()` with scripted ProviderResponse sequences; use real EventBus, real tool functions (list_directory, read_file against project files); test text-only e2e (AC-1, AC-3); tool call with real list_directory (AC-2); tool call with real read_file on pyproject.toml (AC-2); multi-tool sequence; unknown tool recovery; approval denial; tool timeout with sleeping function; API error mid-conversation; event sequence verification; conversation history structure (10 tests)
- [x] T009 Integration tests for REPL exit in `tests/test_integration_repl.py`: mock `ainput` and provider; monkeypatch `sys.argv`; test "exit" and "quit" commands (AC-4); Ctrl+C and EOFError graceful exit (AC-4); empty input ignored; missing ANTHROPIC_API_KEY exits with error (6 tests)

**Checkpoint**: All tests pass. `pytest tests/ -v` shows 55 passed, 0 failed.

---

## Dependencies & Execution Order

- **Phase 1** (fixtures): No dependencies — start immediately
- **Phase 2** (unit tests): Depends on Phase 1 (imports from conftest.py)
  - T003–T007 can all run in parallel (separate files, no cross-dependencies)
- **Phase 3** (integration tests): Depends on Phase 1
  - T008 and T009 are independent of each other

## Verification

```bash
pytest tests/ -v          # All 55 tests pass
pytest tests/ --tb=short  # Quick check
```
