# Feature Specification: Simple Claude Code

**Feature Branch**: `001-simple-claude-code`
**Created**: 2026-03-26
**Status**: Draft
**Input**: Educational re-implementation of Claude Code with transparent agent loop, memory system, and tool execution

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Conversational Coding Assistant (Priority: P1)

A developer starts the assistant from a terminal, types a natural-language request (e.g., "read auth.py and explain it"), and receives a response. The assistant calls tools as needed (reading files, running commands) and returns a coherent answer. The developer sees each tool call and its result in real time. The conversation continues in a loop until the developer exits.

**Why this priority**: Without a working agent loop that sends messages, receives responses, and dispatches tool calls, nothing else functions. This is the core value proposition.

**Independent Test**: Start the assistant, type a request that requires at least one tool call (e.g., "list the files in this directory"), and verify the assistant calls the tool, receives the result, and responds with a useful answer.

**Acceptance Scenarios**:

1. **Given** the assistant is running, **When** the developer types a request, **Then** the assistant sends it to the model and displays the response in the terminal.
2. **Given** the model responds with one or more tool calls, **When** the agent loop processes them, **Then** each tool executes, the result is appended to the conversation, and the model is called again until no more tool calls remain.
3. **Given** the model responds with only text (no tool calls), **When** the agent loop processes it, **Then** the response is displayed and the assistant returns to the input prompt.
4. **Given** the assistant is running, **When** the developer presses Ctrl+C or types an exit command, **Then** the session ends gracefully.

---

### User Story 2 - Visible Extended Thinking (Priority: P2)

A developer asks the assistant a question and sees not only the final answer but also the model's reasoning process. Thinking blocks appear in a visually distinct section of the terminal output, showing the chain of thought that led to the answer or tool call decisions. Token usage (total and thinking) is displayed each turn.

**Why this priority**: Visible reasoning is the primary educational differentiator. Without it, this is just another CLI wrapper. Developers learn agent behaviour by watching the model think.

**Independent Test**: Ask the assistant a multi-step question (e.g., "find all Python files and count them"), verify that thinking blocks appear before each action, and confirm token counts are logged.

**Acceptance Scenarios**:

1. **Given** the assistant receives a model response containing thinking blocks, **When** the UI renders it, **Then** thinking text appears in a visually distinct panel (dimmed/separated) before the assistant's text or tool calls.
2. **Given** thinking blocks are returned by the model, **When** the next API call is made, **Then** thinking blocks are preserved in conversation history (required by the API).
3. **Given** any model response is received, **When** the turn completes, **Then** a log entry shows total tokens and thinking tokens separately.

---

### User Story 3 - Dynamic Tool Discovery (Priority: P3)

A developer adds a new tool by creating a folder under `tools/` containing a `SKILL.md` file (and optionally a `tool.py`). On the next startup, the assistant discovers and loads the new tool automatically. The developer never edits any existing file to register the tool.

**Why this priority**: Open-closed extensibility is a core architectural principle. Demonstrating that new capabilities can be added without modifying existing code teaches plugin-style design.

**Independent Test**: Create a new tool folder with a `SKILL.md` and `tool.py`, restart the assistant, ask it to use the new tool, and confirm it works.

**Acceptance Scenarios**:

1. **Given** a new folder exists under `tools/` containing a `SKILL.md` and `tool.py`, **When** the assistant starts, **Then** the tool's schema is included in API calls and its function is available for dispatch.
2. **Given** a new folder exists under `tools/` containing only a `SKILL.md` (no `tool.py`), **When** the assistant starts, **Then** a generic CLI wrapper is generated for the tool automatically.
3. **Given** a tool's name appears in `tools/config.yaml` under `approval_required`, **When** the model calls that tool, **Then** the developer is prompted for approval before execution.
4. **Given** a tool's name does NOT appear in `approval_required`, **When** the model calls that tool, **Then** it executes immediately without prompting.

---

### User Story 4 - CoALA Memory System (Priority: P4)

A developer works with the assistant across multiple sessions. The assistant loads project knowledge from `CLAUDE.md` (semantic memory) and past learnings from `MEMORY.md` (episodic memory) at startup. During a session, if the developer corrects the assistant, it can explicitly save the correction via the `update_memory` tool for future sessions. Token usage of the conversation (working memory) is logged each turn.

**Why this priority**: The four-store memory model (semantic, episodic, working, procedural) is one of the most interesting concepts in agentic design. Making each store visible and distinct teaches how agents maintain context.

**Independent Test**: Write a `CLAUDE.md` with a project fact, start the assistant, verify it knows the fact. Then trigger a correction, verify the assistant calls `update_memory`, restart, and confirm the memory persists.

**Acceptance Scenarios**:

1. **Given** a `CLAUDE.md` file exists in the project root, **When** the assistant starts, **Then** its contents are loaded into the system prompt as semantic memory.
2. **Given** a `.memory/MEMORY.md` file exists, **When** the assistant starts, **Then** its first 200 lines are loaded into the system prompt as episodic memory.
3. **Given** the developer corrects the assistant during a session, **When** the assistant decides to remember the correction, **Then** it calls `update_memory` with both the fact and a reason, and the entry is appended to `.memory/MEMORY.md`.
4. **Given** the assistant calls `update_memory`, **When** the event is logged, **Then** both the content and the reason are visible in the structured log.

---

### User Story 5 - Structured Event Logging (Priority: P5)

A developer reviews a JSON log file after a session and can replay exactly what the assistant did: which tools it called, what arguments it passed, how many tokens it used, and what it was thinking. Every significant agent action fires an event that is captured by the logging listener.

**Why this priority**: Structured logs are the primary mechanism for post-hoc explainability. Developers who cannot watch the session live can still understand the agent's behaviour by reading the log.

**Independent Test**: Run a multi-turn session with tool calls, then read the log file and verify every `SessionStart`, `PreToolUse`, `PostToolUse`, and `Stop` event is present with correct timestamps and payloads.

**Acceptance Scenarios**:

1. **Given** the assistant starts a session, **When** memory and tools are loaded, **Then** a `SessionStart` event is logged with memory line counts and initial token usage.
2. **Given** a tool is about to execute, **When** the agent loop reaches it, **Then** a `PreToolUse` event is logged with the tool name and arguments.
3. **Given** a tool finishes executing, **When** the result is returned, **Then** a `PostToolUse` event is logged with the tool name and token counts.
4. **Given** the model stops calling tools, **When** the turn completes, **Then** a `Stop` event is logged with total tokens, thinking tokens, and tool call count.

---

### Edge Cases

- What happens when `CLAUDE.md` does not exist? The assistant starts without semantic memory (empty system prompt section).
- What happens when `MEMORY.md` does not exist? The assistant starts without episodic memory and creates the file on first `update_memory` call.
- What happens when a tool folder exists but has no `SKILL.md`? It is silently ignored during discovery.
- What happens when the model calls a tool name that does not exist? The agent loop returns an error result to the model and continues.
- What happens when a tool execution fails (e.g., file not found, command error)? The error output is returned to the model as the tool result so it can adapt.
- What happens when the API key is missing or invalid? The assistant reports a clear error at startup before entering the REPL.
- What happens when the model's response exceeds the token budget? The API returns a truncated response; the assistant logs the usage and continues.

### Technical Constraints

- **TC-001 — CLI tool closure bug**: The dynamic loader generates CLI tool wrappers inside a `for` loop. In Python, closures capture variables by reference, not by value. The generated function for each CLI tool MUST bind the loop variable explicitly (e.g. using a default argument `def fn(command, _name=tool_name)`) or all CLI tools will silently dispatch to the last tool in the loop.
- **TC-002 — Thinking blocks in conversation history**: When appending an assistant turn to conversation history, the code MUST use the full raw content list (including thinking blocks), NOT the text summary. The Anthropic API returns a validation error if thinking blocks are stripped from history on the next call.
- **TC-003 — SKILL.md authoring conventions**: Every `SKILL.md` MUST follow these rules: (a) one default procedure, not a menu of options; (b) focus on non-obvious constraints specific to this implementation; (c) end with a `## Gotchas` section containing concrete corrections to mistakes the model will make without being told. These conventions affect the quality of procedural memory and MUST be followed when writing tool documentation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide an interactive terminal REPL where the developer types requests and receives responses.
- **FR-002**: System MUST send conversation messages to the Anthropic API with extended thinking enabled on every call.
- **FR-003**: System MUST execute a tool dispatch loop: call the model, execute any requested tools, feed results back, repeat until no tool calls remain.
- **FR-004**: System MUST discover tools at startup by scanning for `SKILL.md` files in tool subdirectories, without requiring edits to any existing file.
- **FR-005**: System MUST support two tool flavours: Python tools (with `tool.py` exporting a schema and async function) and CLI tools (with `SKILL.md` only, auto-generating a subprocess wrapper).
- **FR-006**: System MUST load `CLAUDE.md` into the system prompt at session start as semantic memory.
- **FR-007**: System MUST load the first 200 lines of `.memory/MEMORY.md` into the system prompt at session start as episodic memory.
- **FR-008**: System MUST provide an `update_memory` tool that appends dated entries to `.memory/MEMORY.md` with both content and reason fields. The reason field MUST be logged as part of the `PreToolUse` event payload specifically -- not just the content -- so the developer can see not only what the agent remembered but why it decided to.
- **FR-009**: System MUST surface thinking blocks from model responses in a visually distinct format in the terminal UI.
- **FR-010**: System MUST preserve thinking blocks in conversation history for subsequent API calls.
- **FR-011**: System MUST log token usage (total and thinking tokens separately) after each model response. The `thinking_tokens` field MUST appear in BOTH `PostToolUse` and `Stop` event payloads, not only at the end of the turn.
- **FR-012**: System MUST emit structured events (`SessionStart`, `PreToolUse`, `PostToolUse`, `Stop`) to an event bus.
- **FR-013**: System MUST support tool approval: tools listed in `tools/config.yaml` under `approval_required` MUST prompt the developer before execution.
- **FR-014**: System MUST use fully asynchronous I/O for all operations (API calls, tool execution, user input).
- **FR-015**: System MUST inject `SKILL.md` contents into the system prompt as procedural memory (tool usage guidance).
- **FR-016**: System MUST NOT implement streaming, sub-agents, vector retrieval, or MCP server integration.
- **FR-017**: System MUST accept CLI flags for model name, max tokens, thinking budget, and max tool output length.
- **FR-018**: System MUST truncate tool output to a configurable maximum length to prevent context window exhaustion.

### Key Entities

- **Conversation History**: Ordered list of user messages, assistant turns (including thinking blocks), tool calls, and tool results. Ephemeral (session-scoped).
- **Tool Definition**: A schema describing a tool's name, description, and input parameters. Loaded from `tool.py` or auto-generated from `SKILL.md`.
- **Tool Function**: An async callable that implements the tool's behaviour. Either imported from `tool.py` or auto-generated as a subprocess wrapper.
- **Event**: A typed record (SessionStart, PreToolUse, PostToolUse, Stop) with timestamp and payload, emitted by the agent loop.
- **Memory Entry**: A dated fact with a reason, appended to `.memory/MEMORY.md` by the `update_memory` tool.
- **Provider Response**: The parsed model response containing thinking text, content blocks, and raw content for history management.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer with no prior exposure to the codebase can read the source, understand the agent loop, and explain how a request flows from input to response within 30 minutes.
- **SC-002**: Adding a new tool (both Python and CLI flavours) requires creating only new files; zero existing files are modified.
- **SC-003**: Every model response displays thinking blocks visibly separated from the assistant's text output in the terminal.
- **SC-004**: Every tool call is logged as a structured JSON event with tool name, arguments, and token counts.
- **SC-005**: Memory persists across sessions: a fact saved via `update_memory` in session N is present in the system prompt of session N+1.
- **SC-006**: The total source file count (excluding tools, tests, and config) is under 10 files.
- **SC-007**: The assistant handles a 5-turn conversation involving at least 3 different tools without errors.
- **SC-008**: Token usage (total and thinking) is reported after every model response, visible in both the terminal and the log file.

## Assumptions

- Target users are developers who want to learn how agentic coding assistants work by reading and running the code.
- The developer has a valid Anthropic API key with access to models supporting extended thinking and tool use.
- The project targets a single developer running locally; multi-user or production deployment is out of scope.
- Python 3.12+ is available on the developer's machine.
- The six built-in tools (read_file, write_file, find_files, list_directory, run_bash, update_memory) are sufficient for the initial release; additional tools are added by users.
- Context window compaction is out of scope; token count logging is provided so developers can observe growth but no automatic compaction occurs.
- A single flat `MEMORY.md` file is sufficient for episodic memory; topic-based splitting is out of scope.
- The `prettier` CLI tool example is included to demonstrate the CLI tool flavour but is not required for core functionality.
