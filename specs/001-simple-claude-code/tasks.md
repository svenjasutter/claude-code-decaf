# Tasks: Claude Code Decaf

**Input**: Design documents from `/specs/001-simple-claude-code/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in the feature specification. Test tasks are omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, directory structure, and dependency configuration

- [x] T001 Create project directory structure: `providers/`, `listeners/`, `tools/`, `tests/`, `.memory/`, `.logs/`
- [x] T002 Create `pyproject.toml` with dependencies: anthropic, rich, aioconsole, pyyaml, and dev dependencies: pytest, pytest-asyncio
- [x] T003 [P] Create `tools/config.yaml` with initial approval policy listing `write_file` and `run_bash`
- [x] T004 [P] Create `providers/__init__.py` and `listeners/__init__.py` package files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [x] T005 Implement event bus and event dataclasses in `events.py`: EventBus class with `subscribe(event_type, callback)` and `async emit(event)` methods; Event dataclass with `timestamp`, `event_type`, `data` fields; listener exceptions must not crash the agent loop (log and continue)
- [x] T006 Implement AnthropicProvider in `providers/anthropic.py`: AsyncAnthropic wrapper with `async send(messages, tools, system_prompt)` method; ProviderResponse dataclass with `thinking`, `content`, `raw_content`, `usage` fields; TokenUsage dataclass with `input_tokens`, `output_tokens`, `thinking_tokens`; extract thinking blocks from response content; enable extended thinking on every call with configurable `budget_tokens`; propagate API exceptions (no retry)
- [x] T007 Implement dynamic tool loader in `tools/loader.py`: `load_tools()` function that scans `tools/` subdirectories for `SKILL.md`; import `SCHEMA` dict and async function from `tool.py` for Python tools; generate async subprocess wrapper for CLI-only tools (SKILL.md without tool.py); bind loop variables explicitly in CLI wrappers per TC-001; parse `config.yaml` for approval_required set; return `(tool_definitions, tool_functions, approval_required, skill_md_contents)`

**Checkpoint**: Foundation ready — event bus, provider, and tool loader are operational

---

## Phase 3: User Story 1 — Conversational Coding Assistant (Priority: P1) MVP

**Goal**: Developer starts the assistant, types requests, gets responses with tool calls executed in a loop

**Independent Test**: Start the assistant, type "list the files in this directory", verify it calls list_directory, receives the result, and responds

### Implementation for User Story 1

- [x] T008 [US1] Implement Agent class in `agent.py`: constructor accepts provider, event_bus, tool_definitions, tool_functions, approval_required, system_prompt, config (timeout, max_tool_output); `async run(user_input)` method that appends user message to conversation_history, calls provider in a loop until no tool_use blocks remain; for each tool call: emit PreToolUse, check approval, execute with `asyncio.wait_for(fn(), timeout)`, truncate output to max_tool_output chars, emit PostToolUse, append tool_result to history; on timeout return error string; on denial return "Tool execution denied by user"; emit Stop when done; return final assistant text
- [x] T009 [US1] Implement approval listener in `listeners/approval.py`: `async request_approval(tool_name, tool_input)` function using `aioconsole.ainput()` for non-blocking y/n prompt; display tool name and arguments; return bool
- [x] T010 [US1] Implement basic UI listener in `listeners/ui.py`: register for all event types on the event bus; render assistant text responses using `rich.console.Console`; display tool call names and arguments on PreToolUse; display tool results summary on PostToolUse
- [x] T011 [US1] Implement CLI entry point in `main.py`: `argparse` for `--model` (default claude-sonnet-4-20250514), `--max-tokens` (default 16000), `--thinking-budget` (default 10000), `--max-tool-output` (default 10000), `--tool-timeout` (default 120); build system prompt from SKILL.md contents; create Provider, EventBus, Agent; register UI and approval listeners; async REPL loop using `aioconsole.ainput("> ")`; graceful exit on Ctrl+C (KeyboardInterrupt) or "exit" input
- [x] T012 [P] [US1] Create `tools/read_file/tool.py` with SCHEMA and async `read_file(path)` function using `aiofiles` or `asyncio.to_thread`; return file contents truncated
- [x] T013 [P] [US1] Create `tools/write_file/tool.py` with SCHEMA and async `write_file(path, content)` function; write content to file; return confirmation message
- [x] T014 [P] [US1] Create `tools/find_files/tool.py` with SCHEMA and async `find_files(pattern, path)` function using `glob` via `asyncio.to_thread`; return matching file paths
- [x] T015 [P] [US1] Create `tools/list_directory/tool.py` with SCHEMA and async `list_directory(path)` function; return directory listing
- [x] T016 [P] [US1] Create `tools/run_bash/tool.py` with SCHEMA and async `run_bash(command)` function using `asyncio.create_subprocess_shell`; combine stdout and stderr; truncate output
- [x] T017 [P] [US1] Create `tools/read_file/SKILL.md` following TC-003 conventions: procedure, when to use, Gotchas section
- [x] T018 [P] [US1] Create `tools/write_file/SKILL.md` following TC-003 conventions
- [x] T019 [P] [US1] Create `tools/find_files/SKILL.md`, `tools/list_directory/SKILL.md`, and `tools/run_bash/SKILL.md` following TC-003 conventions

**Checkpoint**: The assistant runs, accepts input, calls tools, and returns responses. MVP functional.

---

## Phase 3.5: US1 Testing (Unit + Integration)

**Purpose**: Automated test coverage for all US1 acceptance criteria (AC-1 through AC-4) and edge cases (unknown tool, tool failure, approval denied, API key missing, API failure at runtime, tool timeout).

**Dependencies**: Phase 3 complete (T008–T019)

### Shared Fixtures

- [ ] T100 [P] [US1] Create `tests/conftest.py` with shared pytest-asyncio fixtures: `make_text_response(text)` builds a mock ProviderResponse with a text-only content block; `make_tool_use_response(tool_name, tool_input, tool_use_id)` builds a mock ProviderResponse with a tool_use block; `event_collector(event_bus)` subscribes to all event types and captures events in a list. Set `asyncio_mode = "auto"` in `pyproject.toml` `[tool.pytest.ini_options]`

### Unit Tests

- [ ] T101 [P] [US1] Unit tests for EventBus in `tests/test_events.py`: subscribe and emit, multiple subscribers on same event type, subscriber exception does not crash other subscribers or caller, different event types are isolated, emitting with no subscribers does not raise
- [ ] T102 [P] [US1] Unit tests for AnthropicProvider in `tests/test_provider.py`: mock `AsyncAnthropic.messages.create`; verify `send()` passes correct params (model, max_tokens, thinking config, system, tools, messages); test `_map_response` for text-only, thinking+text, and tool_use responses; verify TokenUsage populated; verify API exceptions propagate (no retry)
- [ ] T103 [P] [US1] Unit tests for Agent class in `tests/test_agent.py`: mock `provider.send()` and tool functions; test text-only response returns text and emits Stop (AC-1, AC-3); single tool call then text (AC-2); multiple tool calls in one response; multi-turn tool loop; unknown tool returns error to model; tool execution failure returns error; approval denied returns denial message; approval approved executes tool; tool timeout returns timeout error; tool output truncated to max_tool_output; API error returns error and preserves history; events emitted in correct order (Response, PreToolUse, PostToolUse, Stop); conversation history preserved across calls; raw_content used in history (TC-002)
- [ ] T104 [P] [US1] Unit tests for tool loader in `tests/test_loader.py`: verify `load_tools()` discovers all Python tools (read_file, write_file, find_files, list_directory, run_bash, update_memory); discovers CLI-only tool (prettier); tool_functions entries are async callables; approval_required set contains write_file and run_bash from config.yaml; skill_md_contents populated; directories without SKILL.md are ignored
- [ ] T105 [P] [US1] Unit tests for main.py helpers in `tests/test_main.py`: `build_system_prompt()` with all parts present and with empty memory; `load_memory_files()` returns empty strings when files missing; loads CLAUDE.md contents and line count; truncates MEMORY.md to first 200 lines; API key validation exits with clear error when ANTHROPIC_API_KEY missing

### Integration Tests

- [ ] T106 [US1] Integration tests for agent loop in `tests/test_integration_agent.py`: mock only `provider.send()` with scripted ProviderResponse sequences; use real EventBus, real tool functions (list_directory, read_file against project files); test text-only conversation end-to-end (AC-1, AC-3); tool call with real list_directory execution (AC-2); tool call with real read_file on pyproject.toml (AC-2); multi-tool sequence (list_directory then read_file); unknown tool recovery; approval denial prevents execution; tool timeout with sleeping function; API error mid-conversation preserves history; event sequence verification; conversation history structure (correct role alternation)
- [ ] T107 [US1] Integration tests for REPL exit in `tests/test_integration_repl.py`: mock `ainput` and provider; test "exit" command ends session (AC-4); "quit" command ends session (AC-4); Ctrl+C (KeyboardInterrupt) ends gracefully (AC-4); EOFError ends gracefully; empty input is ignored (no agent.run call); missing ANTHROPIC_API_KEY exits with error

**Checkpoint**: All US1 acceptance criteria and edge cases have automated test coverage. `pytest tests/` passes.

---

## Phase 4: User Story 2 — Visible Extended Thinking (Priority: P2)

**Goal**: Thinking blocks rendered in a dimmed panel; token usage displayed each turn

**Independent Test**: Ask a multi-step question, verify thinking appears in a distinct panel, confirm token counts are shown

### Implementation for User Story 2

- [x] T020 [US2] Enhance `listeners/ui.py` to render thinking blocks in a dimmed `rich.panel.Panel` before assistant text; use `rich.markdown.Markdown` for assistant text rendering; display token usage (total_tokens / thinking_tokens) after each response
- [x] T021 [US2] Verify `agent.py` appends `response.raw_content` (including thinking blocks) to conversation history per TC-002; ensure thinking blocks are not stripped before the next API call
- [x] T022 [US2] Ensure PostToolUse and Stop events include `thinking_tokens` field in their data payload per FR-011; update event emission in `agent.py` to pass TokenUsage data from ProviderResponse

**Checkpoint**: Thinking is visible, token accounting is transparent

---

## Phase 5: User Story 3 — Dynamic Tool Discovery (Priority: P3)

**Goal**: Adding a tool folder with SKILL.md auto-discovers it at startup; CLI tools get auto-generated wrappers

**Independent Test**: Create a new tool folder with SKILL.md + tool.py, restart, verify it works; create a SKILL.md-only folder, verify CLI wrapper is generated

### Implementation for User Story 3

- [x] T023 [US3] Review and validate `tools/loader.py` end-to-end: verify Python tool import path, CLI wrapper generation, TC-001 closure binding, config.yaml parsing; fix any issues discovered during integration
- [x] T024 [US3] Create `tools/prettier/SKILL.md` as a CLI-only tool example demonstrating auto-wrapper generation; follow TC-003 SKILL.md conventions

**Checkpoint**: Drop-in tool extensibility works for both Python and CLI flavours

---

## Phase 6: User Story 4 — CoALA Memory System (Priority: P4)

**Goal**: CLAUDE.md loaded as semantic memory, MEMORY.md as episodic memory, update_memory tool persists learnings

**Independent Test**: Create a CLAUDE.md, start the assistant, verify it knows the fact; trigger a correction, verify update_memory is called; restart, confirm memory persists

### Implementation for User Story 4

- [x] T025 [US4] Add memory loading to `main.py` session startup: read `CLAUDE.md` if it exists (semantic memory) and `.memory/MEMORY.md` first 200 lines if it exists (episodic memory); inject both into system prompt before SKILL.md contents
- [x] T026 [US4] Create `tools/update_memory/tool.py` with SCHEMA accepting `content` and `reason` parameters; async function appends dated entry in format `- {date}: {content} ({reason})` to `.memory/MEMORY.md`; create `.memory/` directory if it does not exist
- [x] T027 [US4] Create `tools/update_memory/SKILL.md` following TC-003 conventions: when to use, when NOT to use, procedure (one fact per call, check for duplicates), Gotchas section (vague reasons, sandboxed to .memory/)
- [x] T028 [US4] Ensure PreToolUse event for `update_memory` includes the `reason` field in the args payload per FR-008; verify in `agent.py` that tool args are passed through to the event data

**Checkpoint**: All four CoALA memory types are functional and observable

---

## Phase 7: User Story 5 — Structured Event Logging (Priority: P5)

**Goal**: Every agent action logged as JSONL to .logs/ directory; one file per session

**Independent Test**: Run a multi-turn session, read the JSONL log, verify all events present with correct payloads

### Implementation for User Story 5

- [x] T029 [US5] Implement logging listener in `listeners/logging.py`: subscribe to all event types; write each event as a JSON line to `.logs/{timestamp}.jsonl`; create `.logs/` directory on SessionStart if it does not exist; include all payload fields per data-model.md (SessionStart: claude_md_lines, memory_md_lines, tools_loaded, tokens_used; PreToolUse: tool, args; PostToolUse: tool, total_tokens, thinking_tokens; Stop: total_tokens, thinking_tokens, tool_calls)
- [x] T030 [US5] Register logging listener in `main.py` alongside UI and approval listeners; pass session start timestamp to logging listener for filename generation
- [x] T031 [US5] Ensure SessionStart event is emitted with correct payload after memory and tools are loaded; include `claude_md_lines`, `memory_md_lines`, `tools_loaded` list, and initial `tokens_used` count

**Checkpoint**: Complete audit trail of every session is available as JSONL

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Edge case handling, validation, and cleanup

- [x] T032 [P] Add error handling in `agent.py` for unknown tool names: return error string to model and continue
- [x] T033 [P] Add API key validation in `main.py`: check `ANTHROPIC_API_KEY` environment variable at startup; report clear error and exit if missing
- [x] T034 [P] Add API error handling in `agent.py`: catch provider exceptions (network, rate limit, server error); surface error to developer; return to REPL prompt; preserve conversation history
- [x] T035 Validate quickstart.md end-to-end: follow the quickstart steps and verify the assistant starts and responds correctly

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phases 3–7)**: All depend on Foundational phase completion
  - US1 (Phase 3) must complete before US2–US5 (they enhance the core loop)
  - US2 (Phase 4), US3 (Phase 5), US4 (Phase 6), US5 (Phase 7) can proceed in parallel after US1
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Depends on Phase 2 only — delivers the core working loop
- **US2 (P2)**: Depends on US1 — enhances UI rendering and token display
- **US3 (P3)**: Depends on Phase 2 — validates loader already built; can run parallel with US2
- **US4 (P4)**: Depends on US1 — adds memory loading and update_memory tool; can run parallel with US2/US3
- **US5 (P5)**: Depends on US1 — adds logging listener; can run parallel with US2/US3/US4

### Within Each User Story

- Tool .py files before SKILL.md files (schema needed for testing)
- Core module changes before listener enhancements
- Story complete before moving to next priority

### Parallel Opportunities

- T003 and T004 can run in parallel (different files)
- T012–T016 can all run in parallel (separate tool directories)
- T017–T019 can all run in parallel (separate SKILL.md files)
- After US1 completes: US2, US3, US4, US5 can proceed in parallel
- T032, T033, T034 can all run in parallel (different concerns)

---

## Parallel Example: User Story 1

```bash
# Launch all tool implementations together:
Task: "Create tools/read_file/tool.py"     (T012)
Task: "Create tools/write_file/tool.py"    (T013)
Task: "Create tools/find_files/tool.py"    (T014)
Task: "Create tools/list_directory/tool.py" (T015)
Task: "Create tools/run_bash/tool.py"      (T016)

# Launch all SKILL.md files together:
Task: "Create tools/read_file/SKILL.md"    (T017)
Task: "Create tools/write_file/SKILL.md"   (T018)
Task: "Create remaining SKILL.md files"    (T019)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Run the assistant, make a tool call, verify response
5. Demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Demo (MVP!)
3. Add User Story 2 → Thinking visible → Demo
4. Add User Story 3 → Tool extensibility validated → Demo
5. Add User Story 4 → Memory persists across sessions → Demo
6. Add User Story 5 → Full audit trail → Demo
7. Polish → Edge cases handled → Release

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable after US1
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Total source files: 8 core (main.py, agent.py, events.py, providers/anthropic.py, listeners/ui.py, listeners/logging.py, listeners/approval.py, tools/loader.py) — under the SC-006 limit of 10
