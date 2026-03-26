# Simple Claude Code — Technical Specification

> An educational re-implementation of Claude Code that makes the agent loop, memory system, and tool execution fully transparent and explainable.

---

## 1. Goal

Build a minimal agentic coding assistant that developers can read, run, and learn from. Every design decision prioritises explainability over completeness. If a feature obscures how the agent works, it is out of scope.

---

## 2. Architecture

```
CLI (main.py)
└── Agent Loop (agent.py)
    ├── Provider (providers/anthropic.py)
    ├── Event Bus (events.py)
    │   └── Listeners
    │       ├── UIListener       (ui.py)
    │       ├── LoggingListener  (logging.py)
    │       └── ApprovalListener (approval.py)
    └── Tools (tools/)
        ├── read_file
        ├── write_file
        ├── find_files
        ├── list_directory
        ├── run_bash
        └── update_memory
```

### Component responsibilities

**CLI (`main.py`)** — entry point. Starts the async REPL input loop via `asyncio.run()`, registers listeners on the event bus, and calls `await agent.run()`. No business logic lives here.

**Agent Loop (`agent.py`)** — owns conversation history and the tool dispatch loop. Emits events. Contains no UI logic. Fully async — all methods are `async def` to support non-blocking API calls.

**Provider (`providers/anthropic.py`)** — thin async wrapper around the Anthropic API using `AsyncAnthropic`. Accepts messages and tool definitions, enables extended thinking, returns the model response. Swappable in principle; one implementation in scope.

**Event Bus (`events.py`)** — pub/sub bus. The agent emits events; listeners react. No listener can block the agent loop.

**Tools (`tools/`)** — discovered dynamically at startup by scanning for `SKILL.md` files. Two flavours: Python tools (`SKILL.md` + `tool.py`) and CLI tools (`SKILL.md` only, no `tool.py`). Approval policy for all tools is configured centrally in `tools/config.yaml`. The agent loop dispatches by tool name.

---

## 3. Memory System

Memory is modelled on the CoALA cognitive architecture. There are four types, each with a different author, lifetime, and purpose.

### 3.1 Semantic memory — `CLAUDE.md`

Written by the developer. Loaded into the system prompt at session start. Contains stable project knowledge that the agent should always have.

```
Lifetime:   permanent (survives sessions)
Author:     developer
Loaded:     once, at SessionStart, into system prompt
Format:     markdown, target < 200 lines
```

Example content:

```markdown
# Project
- Python 3.12, use uv not pip
- Tests: pytest, run before every commit
- Never modify files in /generated/
- Style: ruff, 2-space indent
```

### 3.2 Episodic memory — `MEMORY.md`

Written by the agent via the `update_memory` tool. Accumulates things learned during sessions that would be useful in future sessions. The agent decides what is worth remembering.

```
Lifetime:   permanent (survives sessions)
Author:     agent (via update_memory tool)
Loaded:     first 200 lines at SessionStart, into system prompt
Format:     dated markdown entries
```

Example content:

```markdown
# Learned
- 2024-01-15: project uses pnpm not npm (user corrected)
- 2024-01-15: auth module uses custom JWT wrapper, not the library
- 2024-01-16: boot with `make dev` not `npm start`
- 2024-01-16: /api/users requires admin scope
```

### 3.3 Working memory — context window

The live conversation: user messages, assistant turns, tool calls, tool results, and extended thinking blocks. Finite. Not persisted across sessions. Token usage is logged each turn so developers can observe it growing.

```
Lifetime:   session only
Author:     both (conversation history)
Loaded:     always present, grows each turn
Compaction: out of scope — token count logged only
```

### 3.4 Procedural memory — tool definitions + system prompt

What the agent knows how to do. Written by the developer as `SKILL.md` files. Present at every session. Never changes at runtime.

```
Lifetime:   permanent
Author:     developer
Loaded:     once, at SessionStart, as tool definitions
Format:     SKILL.md usage guide + tool.py schema + implementation
```

### 3.5 Memory summary

|Type|File|Author|Survives session?|
|---|---|---|---|
|Semantic|`CLAUDE.md`|Developer|✅|
|Episodic|`MEMORY.md`|Agent|✅|
|Working|context window|Both|❌|
|Procedural|SKILL.md + .py|Developer|✅|

---

## 4. Tools

### 4.1 Structure

Each tool lives in its own folder under `tools/`. Two flavours are supported:

**Python tools** — `SKILL.md` + `tool.py`. The `tool.py` exports a `SCHEMA` dict and an async function. Use for tools that need custom logic (file I/O, memory writes, etc.).

**CLI tools** — `SKILL.md` only, no `tool.py`. The loader generates a generic async wrapper that executes whatever command string the model passes via subprocess. Use for tools that are a thin shell around an existing CLI (e.g. `prettier`, `ruff`, `git`).

```
tools/
├── config.yaml          ← approval policy for all tools
├── read_file/
│   ├── SKILL.md         ← usage guide, injected into system prompt
│   └── tool.py          ← SCHEMA dict + async function  (Python tool)
├── write_file/
│   ├── SKILL.md
│   └── tool.py
├── run_bash/
│   ├── SKILL.md
│   └── tool.py
├── update_memory/
│   ├── SKILL.md
│   └── tool.py
├── find_files/
│   ├── SKILL.md
│   └── tool.py
├── list_directory/
│   ├── SKILL.md
│   └── tool.py
└── prettier/
    └── SKILL.md         ← CLI tool: no tool.py, loader generates wrapper
```

A tool folder is discovered automatically if it contains a `SKILL.md`. Adding a new tool never requires editing any existing file — drop in a folder and restart.

### 4.2 tool.py conventions

Each `tool.py` exports two things: a `SCHEMA` dict (sent to the Anthropic API) and an async function (called by the agent loop when the model uses the tool). Both live in the same file so everything about a tool is in one place.

```python
# tools/run_bash/tool.py
import asyncio

SCHEMA = {
    "name": "run_bash",
    "description": "Execute a shell command and return stdout and stderr combined.",
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The shell command to execute."
            }
        },
        "required": ["command"]
    }
}

async def run_bash(command: str) -> str:
    proc = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT
    )
    stdout, _ = await proc.communicate()
    return stdout.decode()[:10000]   # truncate to prevent context exhaustion
```

The `SCHEMA` description is intentionally brief — it tells the model what the tool does. The detailed usage guidance (gotchas, when to use it, procedure) lives in `SKILL.md` and is injected into the system prompt separately as procedural memory.

### 4.3 Approval configuration — `tools/config.yaml`

Approval policy for all tools lives in a single file. Both Python tools and CLI tools are listed here. The agent loop reads this set at startup — if a tool name appears in `approval_required`, the developer is prompted before it executes.

```yaml
# tools/config.yaml
approval_required:
  - write_file
  - run_bash
  - prettier    # CLI tools can be listed here too
```

Any tool not listed runs without prompting. To add approval to a new tool, add its name here — no code changes needed.

### 4.4 Dynamic tool loading

At startup, `tools/loader.py` loads `config.yaml`, scans the `tools/` directory, and for each subfolder containing a `SKILL.md` either imports `tool.py` (Python tool) or generates a generic CLI wrapper (CLI tool).

```python
# tools/loader.py
import asyncio
import importlib.util
import yaml
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent

def load_tools() -> tuple[list[dict], dict, set[str]]:
    """
    Scan tools/ for subdirs containing SKILL.md.
    Returns:
        tool_definitions  — list of SCHEMA dicts, passed to the Anthropic API
        tool_functions    — {name: async_fn}, used by the agent loop to dispatch
        approval_required — set of tool names that require approval before execution
    """
    config = yaml.safe_load((TOOLS_DIR / "config.yaml").read_text())
    approval_required = set(config.get("approval_required", []))

    tool_definitions = []
    tool_functions = {}

    for tool_dir in sorted(TOOLS_DIR.iterdir()):
        if not tool_dir.is_dir():
            continue
        if not (tool_dir / "SKILL.md").exists():
            continue

        tool_py = tool_dir / "tool.py"

        if tool_py.exists():
            # Python tool — import SCHEMA and async function from tool.py
            spec = importlib.util.spec_from_file_location(
                f"tools.{tool_dir.name}.tool", tool_py
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            schema = module.SCHEMA
            fn = getattr(module, schema["name"])
        else:
            # CLI tool — generate a generic wrapper from SKILL.md
            skill_md = (tool_dir / "SKILL.md").read_text()
            tool_name = tool_dir.name
            schema = {
                "name": tool_name,
                "description": skill_md,
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The CLI command to execute."
                        }
                    },
                    "required": ["command"]
                }
            }
            async def fn(command: str) -> str:
                proc = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT
                )
                stdout, _ = await proc.communicate()
                return stdout.decode()[:10000]

        tool_definitions.append(schema)
        tool_functions[schema["name"]] = fn

    return tool_definitions, tool_functions, approval_required
```

The agent loop calls `load_tools()` once at `SessionStart` and holds the results for the session.

### 4.5 SKILL.md conventions

Each `SKILL.md` follows these authoring principles:

**Add what the agent lacks, omit what it knows.** Focus on non-obvious constraints and edge cases specific to this implementation. Do not explain what a file or shell command is.

**One default, not a menu.** When multiple approaches exist, pick one. Mention alternatives only as an escape hatch with a condition.

**Procedures over declarations.** Describe how to use the tool, not what it produces. Steps the agent can follow outperform descriptions of outcomes.

**Gotchas section required.** Every `SKILL.md` ends with `## Gotchas` — concrete corrections to mistakes the agent will make without being told. Not general advice; specific facts about this tool's behaviour in this codebase.

Example — `run_bash/SKILL.md`:

```markdown
# run_bash

Execute a shell command and return stdout and stderr combined.

## When to use
Use for build commands, test runners, and git operations.
Prefer read_file and write_file for file operations — they are
safer and produce cleaner tool results.

## Procedure
1. Pass the full command as a single string
2. Commands run from the project root by default
3. stdout and stderr are combined and returned to you

## Gotchas
- Commands are not interactive. Never use commands that prompt for input.
- There is no shell state between calls. Each call is a fresh subprocess —
  `cd` in one call does not carry over to the next.
- Long-running commands block the agent loop. Prefer commands that terminate.
- Destructive commands trigger approval before executing. This is intentional —
  do not try to work around it.
```

Example — `update_memory/SKILL.md`:

```markdown
# update_memory

Persist a fact learned during this session so it is available in future sessions.

## When to use
- User corrects your approach or assumptions
- You discover a non-obvious project convention
- A command behaves differently than expected
- A pattern is worth remembering across sessions

## When NOT to use
- Facts already in CLAUDE.md — they are already known
- Task-specific details that will not generalise to future sessions
- Anything the developer should write to CLAUDE.md themselves

## Procedure
1. Write one fact per call — multiple facts belong in separate calls
2. Make the `reason` specific: what happened that made this worth remembering?
3. Check loaded MEMORY.md first — do not duplicate existing entries

## Gotchas
- Vague reasons ("learned something useful") make the log unreadable and
  make it impossible to decide later whether to keep the memory.
- This tool is sandboxed to .memory/ — it cannot write elsewhere.
- The agent loop logs your `reason` as a PreToolUse event. It is visible
  to the developer in real time. Write it as if they are reading it.
```

### 4.6 Tool definitions

|Tool|Triggers approval|Description|
|---|---|---|
|`read_file`|No|Read a file from the filesystem|
|`write_file`|Yes|Write or overwrite a file|
|`find_files`|No|Search for files by name or glob pattern|
|`list_directory`|No|List contents of a directory|
|`run_bash`|Yes|Execute a shell command, return stdout/stderr|
|`update_memory`|No|Append a learned fact to .memory/MEMORY.md|

### 4.7 `update_memory` in detail

The only tool not present in standard file toolkits. Explicit by design — unlike Claude Code, which writes memory implicitly via its general `write_file`.

Parameters:

- `content` — the fact to store
- `reason` — why the agent decided this is worth remembering

The `reason` fires a distinct `PreToolUse` event so the log shows not just _what_ the agent remembered but _why_ it decided to. Sandboxed to `.memory/`.

```python
# Agent calls
await update_memory(
    content="project uses pnpm not npm",
    reason="user corrected me when I ran npm install"
)

# Appended to .memory/MEMORY.md:
# - 2024-01-15: project uses pnpm not npm (user corrected me when I ran npm install)
```

---

## 5. Extended Thinking

Extended thinking is enabled on every API call. The model emits its reasoning as `thinking` content blocks before producing text or tool calls. This is one of the most important things to make visible in a teaching tool — developers should see not just what the agent decided, but the chain of reasoning that led there.

### 5.1 API configuration

```python
response = await client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=16000,
    thinking={
        "type": "enabled",
        "budget_tokens": 10000   # thinking draws from max_tokens budget
    },
    system=system_prompt,
    tools=tool_definitions,
    messages=conversation_history
)
```

`budget_tokens` controls how much of `max_tokens` the model may spend on thinking. A budget of 10,000 is sufficient for most coding tasks; raise it for complex multi-file refactors.

### 5.2 Thinking blocks in responses

The provider maps Anthropic response content into a `ProviderResponse` dataclass:

```python
@dataclass
class ProviderResponse:
    thinking: str           # concatenated text from all thinking blocks, for UI rendering
    content: list[Block]    # text blocks and tool_use blocks
    raw_content: list       # full content list including thinking blocks, for history management
```

Thinking blocks are extracted and surfaced separately so the UIListener can render them in a distinct panel — visually separating the model's reasoning from its actions. `raw_content` preserves the full unmodified list for inclusion in conversation history.

### 5.3 Thinking blocks in conversation history

Thinking blocks must be preserved in the conversation history and echoed back on the next API call. The Anthropic API requires this — stripping thinking blocks from history causes a validation error.

```python
# When appending an assistant turn to history, include the full raw content list
# (thinking blocks + text blocks + tool_use blocks), not just the text summary
conversation_history.append({
    "role": "assistant",
    "content": response.raw_content   # full list, thinking blocks intact
})
```

### 5.4 Token accounting

Thinking tokens count against the `max_tokens` budget. The `PostToolUse` and `Stop` log events include a `thinking_tokens` field alongside `total_tokens` so developers can observe exactly how much the model spent on reasoning each turn.

```json
{"ts": "...", "event": "Stop", "data": {"total_tokens": 4100, "thinking_tokens": 1840, "tool_calls": 3}}
```

---

## 6. Event Bus & Hooks

### 6.1 Events

|Event|Fired by|When|
|---|---|---|
|`SessionStart`|Agent loop|Before first turn; after CLAUDE.md loaded|
|`PreToolUse`|Agent loop|Before any tool executes|
|`PostToolUse`|Agent loop|After tool returns result|
|`Stop`|Agent loop|Agent decides no more tool calls needed|

### 6.2 Listeners

**`UIListener`** — renders the conversation to the terminal. Prints thinking blocks in a dimmed panel, assistant messages, tool calls, and results in a readable format.

**`LoggingListener`** — writes structured JSON logs to file. Every event is logged with a timestamp, event type, and payload. This is the primary explainability mechanism — developers can replay exactly what the agent did and why.

**`ApprovalListener`** — called directly by the agent loop before executing any tool whose name appears in `approval_required` (configured in `tools/config.yaml`). Prompts the developer for confirmation before the tool executes. Implemented as an async function so it does not block the event loop while waiting for user input.

### 6.3 Log example

```json
{"ts": "2024-01-15T10:23:01", "event": "SessionStart",  "data": {"claude_md_lines": 12, "memory_md_lines": 4, "tokens_used": 1840}}
{"ts": "2024-01-15T10:23:04", "event": "PreToolUse",    "data": {"tool": "read_file", "args": {"path": "auth.py"}}}
{"ts": "2024-01-15T10:23:04", "event": "PostToolUse",   "data": {"tool": "read_file", "total_tokens": 3210, "thinking_tokens": 980}}
{"ts": "2024-01-15T10:23:07", "event": "PreToolUse",    "data": {"tool": "update_memory", "args": {"content": "auth uses custom JWT", "reason": "discovered in auth.py"}}}
{"ts": "2024-01-15T10:23:07", "event": "PostToolUse",   "data": {"tool": "update_memory", "total_tokens": 3310, "thinking_tokens": 0}}
{"ts": "2024-01-15T10:23:09", "event": "Stop",          "data": {"total_tokens": 4100, "thinking_tokens": 1840, "tool_calls": 3}}
```

---

## 7. Agent Loop

The loop is fully async. It runs until the model stops calling tools.

```
1. Load CLAUDE.md → inject into system prompt      (semantic memory)
2. Load MEMORY.md first 200 lines → inject         (episodic memory)
3. Scan tools/ for SKILL.md → load tool_definitions and tool_functions
   (procedural memory — dynamic discovery via tools/loader.py)
4. Emit SessionStart

loop:
    5.  await provider.send(messages, tool_definitions, system_prompt)
    6.  Receive ProviderResponse (thinking blocks + content blocks)
    7.  If no tool calls → emit Stop → return to REPL
    8.  For each tool call:
            a. Emit PreToolUse
            b. If tool_name in approval_required → await ApprovalListener(tool_name, tool_input)
            c. await tool_functions[tool_name](**tool_input)
            d. Emit PostToolUse
            e. Append tool result to conversation history
               (preserve thinking blocks in raw_content — required by API)
    9.  Log token count (total + thinking)
    10. Go to 5
```

---

## 8. Async Architecture

The entire stack is async. This is necessary because the Anthropic API calls are I/O-bound — blocking them would freeze the REPL while waiting for responses. It also keeps the architecture honest: tool functions that shell out (e.g. `run_bash`) or do file I/O should be non-blocking too.

### 8.1 Entry point

```python
# main.py
import asyncio

async def main():
    agent = Agent(provider, event_bus)
    register_ui_listener(event_bus)
    register_logging_listener(event_bus)
    register_approval_listener(event_bus)

    while True:
        user_input = await ainput("> ")   # async stdin read
        response = await agent.run(user_input)

asyncio.run(main())
```

### 8.2 Provider

```python
# providers/anthropic.py
from anthropic import AsyncAnthropic

class AnthropicProvider:
    def __init__(self):
        self.client = AsyncAnthropic()   # reads ANTHROPIC_API_KEY from env

    async def send(self, messages, tools, system_prompt) -> ProviderResponse:
        response = await self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=16000,
            thinking={"type": "enabled", "budget_tokens": 10000},
            system=system_prompt,
            tools=tools,
            messages=messages
        )
        return self._map_response(response)
```

### 8.3 Tools

All tool functions are `async def`. Tools that perform I/O use `asyncio`-compatible libraries or `asyncio.to_thread()` for blocking calls (e.g. synchronous file reads on large files).

```python
# tools/run_bash/tool.py
import asyncio

SCHEMA = {
    "name": "run_bash",
    "description": "Execute a shell command and return stdout and stderr combined.",
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Shell command to execute."}
        },
        "required": ["command"]
    }
}

async def run_bash(command: str) -> str:
    proc = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT
    )
    stdout, _ = await proc.communicate()
    return stdout.decode()[:10000]   # truncate to prevent context exhaustion
```

### 8.4 Event listeners

All listener callbacks registered on the event bus are `async def`. The `ApprovalListener` uses `aioconsole.ainput()` (or equivalent) so the approval prompt is non-blocking.

### 8.5 Why async matters here (teaching note)

For the current single-agent scope, async doesn't provide concurrency benefits — there's only one thing happening at a time. Its value is different: it makes the I/O-bound nature of agent loops explicit in the code, and it leaves the door open for the natural next chapter (parallel tool execution, sub-agents) without requiring an architectural rewrite. Seeing `await provider.send()` in the loop immediately communicates that this is a network call that yields control — something a synchronous call hides.

---

## 9. Session Start sequence

```
main.py starts
    → reads CLAUDE.md (semantic memory)
    → reads MEMORY.md first 200 lines (episodic memory)
    → scans tools/ for SKILL.md, imports tool.py files (procedural memory)
    → creates AsyncAnthropic client
    → registers UIListener, LoggingListener, ApprovalListener
    → emits SessionStart (logs token count of injected memory)
    → enters async REPL
```

---

## 10. File layout

```
simple-claude-code/
├── main.py                  # CLI entry point, async REPL
├── agent.py                 # Agent loop, conversation history
├── events.py                # Event bus
├── providers/
│   └── anthropic.py         # AsyncAnthropic wrapper, extended thinking
├── listeners/
│   ├── ui.py                # Terminal UI (renders thinking blocks)
│   ├── logging.py           # JSON structured logging (thinking_tokens field)
│   └── approval.py          # Human-in-the-loop approval (async)
├── tools/
│   ├── loader.py            # Dynamic discovery: scans for SKILL.md, imports tool.py
│   ├── config.yaml          # Approval policy: lists tools that require confirmation
│   ├── read_file/       (SKILL.md + tool.py)   ← Python tool
│   ├── write_file/      (SKILL.md + tool.py)   ← Python tool
│   ├── find_files/      (SKILL.md + tool.py)   ← Python tool
│   ├── list_directory/  (SKILL.md + tool.py)   ← Python tool
│   ├── run_bash/        (SKILL.md + tool.py)   ← Python tool
│   ├── update_memory/   (SKILL.md + tool.py)   ← Python tool
│   └── prettier/        (SKILL.md only)         ← CLI tool example
├── CLAUDE.md                # Semantic memory (developer writes)
└── .memory/
    └── MEMORY.md            # Episodic memory (agent writes)
```

---

## 11. Configuration

|Setting|Source|Default|
|---|---|---|
|`ANTHROPIC_API_KEY`|Environment variable|(required, no default)|
|`--model`|CLI flag|`claude-sonnet-4-20250514`|
|`--max-tokens`|CLI flag|`16000`|
|`--thinking-budget`|CLI flag|`10000`|
|`--max-tool-output`|CLI flag|`10000` (characters)|

Tool approval policy is configured in `tools/config.yaml`. All other configuration is via CLI flags or environment variables.

---

## 12. External Dependencies

|Dependency|Purpose|
|---|---|
|`anthropic`|Async API client (extended thinking, tool use)|
|`rich`|Terminal UI rendering (panels, markdown, syntax)|
|`aioconsole`|Async stdin for REPL and approval prompts|
|`pytest`|Testing framework (dev dependency)|
|`pytest-asyncio`|Async test support (dev dependency)|
|`pyyaml`|Parse `tools/config.yaml`|

---

## 13. Out of scope

| Feature                            | Reason excluded                                                                                                            |
| ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| Compaction                         | Production problem, not a learning problem. Token count logged instead.                                                    |
| Subagents                          | Adds a second loop before the first is understood. Natural chapter 2.                                                      |
| Auto memory                        | Implicit writes obscure the mechanism. `update_memory` is explicit.                                                        |
| AutoDream                          | Consolidation layer on top of memory — too far from the core loop.                                                         |
| Multiple providers                 | One provider keeps the abstraction visible without being distracting.                                                      |
| Vector/semantic retrieval          | Adds infrastructure (embeddings, vector DB) unrelated to the loop.                                                         |
| MCP servers                        | External protocol layer — out of educational scope.                                                                        |
| MEMORY.md topic files              | Single flat file is sufficient and more readable for learning.                                                             |
| Conditional rules (.claude/rules/) | CLAUDE.md hierarchy adds complexity without new insight.                                                                   |
| Episodic → semantic promotion      | Interesting CoALA concept but requires heuristics and a promotion mechanism. Manual: developer edits CLAUDE.md themselves. |
| Streaming                          | Adds async generator complexity before the basic loop is understood. Full response wait is fine for a teaching tool.       |