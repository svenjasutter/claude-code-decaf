# Feature Specification: US1 Automated Test Coverage

**Feature Branch**: `002-us1-tests`
**Created**: 2026-03-28
**Status**: Complete
**Input**: Automated test coverage for User Story 1 (Conversational Coding Assistant) from `specs/001-simple-claude-code/spec.md`

## User Scenarios & Testing *(mandatory)*

### User Story 1 — US1 Test Coverage (Priority: P1)

A developer runs `pytest tests/` and gets automated verification that all US1 acceptance criteria and edge cases pass. Tests cover the agent loop, event bus, provider, tool loader, and CLI helpers at two levels: unit tests (mocked dependencies) and integration tests (real tools, real filesystem).

**Why this priority**: US1 is the core MVP. Without automated tests, regressions go undetected when subsequent features (US2–US5) modify shared modules like `agent.py` and `main.py`.

**Acceptance Scenarios**:

1. **Given** the test suite runs, **When** all unit tests execute, **Then** each module is tested in isolation with mocked dependencies: agent loop, event bus, provider response mapping, tool loader, and CLI helpers.
2. **Given** the test suite runs, **When** integration tests execute, **Then** the full agent loop is exercised with a mocked provider but real tool functions (list_directory, read_file) against the real filesystem.
3. **Given** the test suite runs, **When** all tests complete, **Then** every US1 acceptance criterion (AC-1 through AC-4) and every applicable edge case has at least one passing test.
4. **Given** a developer runs `pytest tests/ -v`, **When** all 55 tests complete, **Then** the exit code is 0 and no tests are skipped or xfailed.

---

### Testing Requirements

**Unit tests** MUST cover:
- The agent loop (text-only response, single/multiple/chained tool calls, event ordering, conversation history preservation, TC-002 raw_content compliance)
- The event bus (subscribe/emit, exception isolation)
- The provider response mapping (text/thinking/tool_use blocks, token usage, exception propagation)
- The tool loader (Python and CLI discovery, approval config, SKILL.md loading)
- The CLI helpers (system prompt construction, memory file loading with 200-line truncation, API key validation)

**Integration tests** MUST exercise:
- The full agent loop with a mocked provider but real tool functions against the real filesystem
- All four US1 acceptance scenarios (AC-1 through AC-4)
- All applicable edge cases (unknown tool, tool failure, approval denial, API key missing, API failure at runtime, tool timeout)

**Mock boundaries**:
- Unit tests mock the provider and tool functions
- Integration tests mock only the provider

### Edge Cases

- What happens when MagicMock is used with `name=` parameter? The `name` attribute requires a helper function (`_make_block`) because `MagicMock(name=...)` sets the mock's internal name, not a `.name` attribute.
- What happens when argparse sees pytest CLI arguments? REPL tests must monkeypatch `sys.argv` to prevent argparse from parsing pytest's `tests/ -v` args.
- What happens when integration tests use write tools? Integration tests use read-only tools (list_directory, read_file) against the project's own files. Write-path tests use the approval-denial path to avoid filesystem mutation.

### Coverage Matrix

| US1 Criterion | Unit Test | Integration Test |
|---------------|-----------|------------------|
| AC-1: Send request, display response | test_agent.py | test_integration_agent.py |
| AC-2: Tool calls loop until done | test_agent.py | test_integration_agent.py |
| AC-3: Text-only returns to prompt | test_agent.py | test_integration_agent.py |
| AC-4: Graceful exit (Ctrl+C, exit) | — | test_integration_repl.py |
| Edge: Unknown tool | test_agent.py | test_integration_agent.py |
| Edge: Tool execution fails | test_agent.py | — |
| Edge: Approval denied | test_agent.py | test_integration_agent.py |
| Edge: API key missing | test_main.py | test_integration_repl.py |
| Edge: API failure at runtime | test_agent.py | test_integration_agent.py |
| Edge: Tool timeout | test_agent.py | test_integration_agent.py |

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Test suite MUST use pytest + pytest-asyncio with `asyncio_mode = "auto"`.
- **FR-002**: Shared fixtures MUST provide mock response builders (`make_text_response`, `make_tool_use_response`, `make_thinking_response`) and an event collector.
- **FR-003**: Unit tests MUST NOT make real API calls or execute real tool functions (except test_loader.py which tests discovery against the real tools/ directory).
- **FR-004**: Integration tests MUST use real EventBus and real tool functions but MUST mock the Anthropic provider.
- **FR-005**: All tests MUST pass with `pytest tests/ -v` returning exit code 0.

### Key Entities

- **ProviderResponse mock**: A crafted `ProviderResponse` with `MagicMock` content blocks simulating Anthropic SDK responses.
- **Event collector**: A test fixture that subscribes to all event types and captures emitted events for assertion.
- **Mock approval function**: An `AsyncMock` returning `True` or `False` to simulate user approval decisions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `pytest tests/ -v` passes with 55 tests, 0 failures, 0 errors.
- **SC-002**: Every US1 acceptance criterion (AC-1 through AC-4) has at least one unit test and one integration test.
- **SC-003**: Every US1 edge case from `specs/001-simple-claude-code/spec.md` has at least one test.
- **SC-004**: No test requires a real Anthropic API key or network access.

## Assumptions

- The US1 implementation in `specs/001-simple-claude-code` is complete and stable.
- pytest and pytest-asyncio are available as dev dependencies in `pyproject.toml`.
- The test suite runs in under 5 seconds (no real API calls, timeouts set to 0.05s in tests).
