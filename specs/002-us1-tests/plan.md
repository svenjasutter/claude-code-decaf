# Implementation Plan: US1 Automated Test Coverage

**Branch**: `002-us1-tests` | **Date**: 2026-03-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-us1-tests/spec.md`
**Depends on**: `/specs/001-simple-claude-code/` (US1 implementation)

## Summary

Add unit tests and integration tests for User Story 1 (Conversational
Coding Assistant). Tests validate all four acceptance criteria (AC-1
through AC-4) and all six applicable edge cases without making real API
calls. The provider is always mocked; integration tests use real tool
functions against the real filesystem.

## Technical Context

**Language/Version**: Python 3.12+
**Testing Framework**: pytest + pytest-asyncio
**Mock Library**: unittest.mock (AsyncMock, MagicMock, patch)
**Configuration**: `asyncio_mode = "auto"` in `pyproject.toml`
**Target**: 55 tests, <5s execution time, zero network calls

## Constitution Check

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Explainability Over Completeness | PASS | Tests are educational — each test function name describes the behaviour being verified |
| II. Async-First | PASS | All test functions are async; pytest-asyncio auto mode handles the event loop |
| VI. Simplicity and Minimalism | PASS | Shared fixtures avoid duplication; no test framework beyond pytest |

## Project Structure

### Documentation (this feature)

```text
specs/002-us1-tests/
├── spec.md      # This feature's specification
├── plan.md      # This file
└── tasks.md     # Task breakdown
```

### Test Files (repository root)

```text
tests/
├── conftest.py                  # Shared fixtures: mock response builders, event collector
├── test_events.py               # EventBus unit tests (6 tests)
├── test_provider.py             # AnthropicProvider unit tests (7 tests)
├── test_agent.py                # Agent loop unit tests (14 tests)
├── test_loader.py               # Tool discovery unit tests (6 tests)
├── test_main.py                 # CLI helpers unit tests (6 tests)
├── test_integration_agent.py    # Agent loop integration tests (10 tests)
└── test_integration_repl.py     # REPL exit path integration tests (6 tests)
```

## Testing Strategy

Two layers — unit tests isolate each module with mocks, integration tests
exercise the full agent loop with real tool functions against the real
filesystem.

### What gets mocked at each layer

| Layer | Provider | EventBus | Tool functions | Filesystem |
|-------|----------|----------|----------------|------------|
| Unit  | Mocked   | Real (with event collector) | Mocked | tmp_path where needed |
| Integration | Mocked | Real | Real (list_directory, read_file, etc.) | Real project files |

### Shared fixtures (`tests/conftest.py`)

- `make_text_response(text)` — builds a mock `ProviderResponse` with a text-only content block
- `make_tool_use_response(tool_name, tool_input, tool_use_id)` — builds a mock `ProviderResponse` with a `tool_use` block
- `make_thinking_response(thinking, text)` — builds a mock `ProviderResponse` with thinking + text
- `event_collector(event_bus)` — subscribes to all event types and captures events in a list

### Key design decisions

- `MagicMock` stubs mimic Anthropic SDK content blocks (`.type`, `.text`, `.name`, `.input`, `.id` attributes). The `name` attribute requires a helper function (`_make_block`) because `MagicMock(name=...)` sets the mock's internal name, not a `.name` attribute.
- Integration tests use read-only tools (list_directory, read_file) against the project's own files. Write-path tests use the approval-denial path to avoid filesystem mutation.
- REPL tests monkeypatch `sys.argv` to prevent argparse from seeing pytest's CLI arguments.
- `asyncio_mode = "auto"` in `pyproject.toml` so all async test functions run without explicit `@pytest.mark.asyncio`.

## Complexity Tracking

> No violations detected. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none)    |            |                                     |
