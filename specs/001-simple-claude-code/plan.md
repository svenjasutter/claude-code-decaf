# Implementation Plan: Simple Claude Code

**Branch**: `001-simple-claude-code` | **Date**: 2026-03-26 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-simple-claude-code/spec.md`

## Summary

Build a minimal, educational agentic coding assistant with a transparent
async agent loop, CoALA memory system (semantic, episodic, working,
procedural), dynamic tool discovery via `SKILL.md` convention, visible
extended thinking, and structured JSON event logging. The entire stack
uses Python asyncio. No streaming, no sub-agents, no vector retrieval,
no MCP.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: anthropic (async API client), rich (terminal UI), aioconsole (async stdin), pyyaml (config parsing)
**Storage**: File-based — `CLAUDE.md`, `.memory/MEMORY.md`, `.logs/*.jsonl`, `tools/config.yaml`
**Testing**: pytest + pytest-asyncio
**Target Platform**: Local developer machine (Linux/macOS/WSL)
**Project Type**: CLI tool
**Performance Goals**: N/A (educational, single-user, non-production)
**Constraints**: Under 10 core source files (SC-006); fully async (Constitution II); no excluded features (Constitution Exclusions)
**Scale/Scope**: Single developer running locally

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Explainability Over Completeness | PASS | Educational focus explicit in spec goal; visible thinking (FR-009); structured logs (FR-020); under 10 files (SC-006) |
| II. Async-First | PASS | FR-014 mandates fully async I/O; all tool functions are `async def`; `AsyncAnthropic` client; `aioconsole` for REPL |
| III. Dynamic Tool Discovery | PASS | FR-004/FR-005: SKILL.md scan at startup; two flavours (Python + CLI); no existing file edits (SC-002) |
| IV. CoALA Memory Architecture | PASS | Four distinct stores: semantic (CLAUDE.md), episodic (MEMORY.md), working (context window), procedural (SKILL.md + tool.py) |
| V. Visible Extended Thinking | PASS | FR-002: thinking enabled on every call; FR-009: visually distinct UI panel; FR-010: preserved in history; FR-011: token accounting in both PostToolUse and Stop |
| VI. Simplicity and Minimalism | PASS | 8 core source files planned; no abstractions beyond what is needed; flat file memory; no retry logic |
| Explicit Exclusions | PASS | FR-016: no streaming, no sub-agents, no vector retrieval, no MCP |

**Gate result**: ALL PASS. No violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/001-simple-claude-code/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (internal interfaces)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
claude-code-decaf/
├── main.py                  # CLI entry point, async REPL, argument parsing
├── agent.py                 # Agent loop, conversation history, tool dispatch
├── events.py                # Event bus (pub/sub), event dataclasses
├── providers/
│   └── anthropic.py         # AsyncAnthropic wrapper, ProviderResponse dataclass
├── listeners/
│   ├── ui.py                # Terminal UI (rich panels for thinking, text, tools)
│   ├── logging.py           # JSON structured logging to .logs/
│   └── approval.py          # Human-in-the-loop approval (async prompt)
├── tools/
│   ├── loader.py            # Dynamic discovery: scan SKILL.md, import tool.py
│   ├── config.yaml          # Approval policy
│   ├── read_file/
│   │   ├── SKILL.md
│   │   └── tool.py
│   ├── write_file/
│   │   ├── SKILL.md
│   │   └── tool.py
│   ├── find_files/
│   │   ├── SKILL.md
│   │   └── tool.py
│   ├── list_directory/
│   │   ├── SKILL.md
│   │   └── tool.py
│   ├── run_bash/
│   │   ├── SKILL.md
│   │   └── tool.py
│   └── update_memory/
│       ├── SKILL.md
│       └── tool.py
├── CLAUDE.md                # Semantic memory (developer writes)
└── .memory/
    └── MEMORY.md            # Episodic memory (agent writes)

tests/
├── conftest.py                  # Shared fixtures: mock response builders, event collector
├── test_events.py               # EventBus unit tests
├── test_provider.py             # AnthropicProvider unit tests
├── test_agent.py                # Agent loop unit tests
├── test_loader.py               # Tool discovery unit tests
├── test_main.py                 # CLI helpers unit tests
├── test_integration_agent.py    # Agent loop integration tests (real tools, real EventBus)
└── test_integration_repl.py     # REPL exit path integration tests
```

**Structure Decision**: Single flat project at repository root. No `src/`
wrapper — every module is directly importable. Tools live under `tools/`
with one subdirectory per tool. Listeners are separated from the agent
loop for single-responsibility clarity. The `providers/` directory exists
for organisational clarity even though only one provider is in scope.

## Testing Strategy

Testing is phased per user story. Each story's tests are added after its
implementation is complete. The API is never called in tests — the provider
is always mocked.

### US1 Testing (Phase 3.5)

**Approach**: Two layers — unit tests isolate each module with mocks,
integration tests exercise the full agent loop with real tool functions
against the real filesystem.

**What gets mocked at each layer**:

| Layer | Provider | EventBus | Tool functions | Filesystem |
|-------|----------|----------|----------------|------------|
| Unit  | Mocked   | Real (with event collector) | Mocked | tmp_path where needed |
| Integration | Mocked | Real | Real (list_directory, read_file, etc.) | Real project files |

**Shared fixtures** (`tests/conftest.py`):
- `make_text_response(text)` — builds a mock `ProviderResponse` with a text-only content block
- `make_tool_use_response(tool_name, tool_input, tool_use_id)` — builds a mock `ProviderResponse` with a `tool_use` block
- `make_thinking_response(thinking, text)` — builds a mock `ProviderResponse` with thinking + text
- `event_collector(event_bus)` — subscribes to all event types and captures events in a list

**Coverage targets** (maps to spec.md acceptance criteria and edge cases):

| Criterion | Unit test file | Integration test file |
|-----------|---------------|----------------------|
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

**Key design decisions**:
- `MagicMock` stubs mimic Anthropic SDK content blocks (`.type`, `.text`, `.name`, `.input`, `.id` attributes). The `name` attribute requires a helper function (`_make_block`) because `MagicMock(name=...)` sets the mock's internal name, not a `.name` attribute.
- Integration tests use read-only tools (list_directory, read_file) against the project's own files. Write-path tests use the approval-denial path to avoid filesystem mutation.
- REPL tests monkeypatch `sys.argv` to prevent argparse from seeing pytest's CLI arguments.
- `asyncio_mode = "auto"` in `pyproject.toml` so all async test functions run without explicit `@pytest.mark.asyncio`.

### US2–US5 Testing

To be designed when testing phases are added for these stories. The same two-layer approach (unit + integration) and shared fixtures will apply.

## Complexity Tracking

> No violations detected. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none)    |            |                                     |
