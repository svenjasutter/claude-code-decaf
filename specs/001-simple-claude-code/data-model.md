# Data Model: Simple Claude Code

**Phase**: 1 — Design & Contracts
**Date**: 2026-03-26

## Entities

### ProviderResponse

Parsed model response returned by the provider layer.

| Field | Type | Description |
|-------|------|-------------|
| `thinking` | `str` | Concatenated text from all thinking blocks (for UI rendering) |
| `content` | `list[TextBlock \| ToolUseBlock]` | Text and tool_use blocks (excludes thinking) |
| `raw_content` | `list[dict]` | Full unmodified content list including thinking blocks (for history) |
| `usage` | `TokenUsage` | Token counts for this response |

### TokenUsage

Token accounting for a single API response.

| Field | Type | Description |
|-------|------|-------------|
| `input_tokens` | `int` | Tokens consumed by the input (messages + system prompt + tools) |
| `output_tokens` | `int` | Tokens consumed by the output (thinking + text + tool_use) |
| `thinking_tokens` | `int` | Subset of output_tokens spent on thinking blocks |

### Event

Base for all events emitted by the agent loop.

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | `str` | ISO 8601 timestamp |
| `event_type` | `str` | One of: `SessionStart`, `PreToolUse`, `PostToolUse`, `Stop` |
| `data` | `dict` | Event-specific payload (see Event Payloads below) |

### Event Payloads

**SessionStart**:

| Field | Type | Description |
|-------|------|-------------|
| `claude_md_lines` | `int` | Number of lines loaded from CLAUDE.md |
| `memory_md_lines` | `int` | Number of lines loaded from MEMORY.md |
| `tools_loaded` | `list[str]` | Names of discovered tools |
| `tokens_used` | `int` | Initial token count of system prompt |

**PreToolUse**:

| Field | Type | Description |
|-------|------|-------------|
| `tool` | `str` | Tool name |
| `args` | `dict` | Tool input arguments |

**PostToolUse**:

| Field | Type | Description |
|-------|------|-------------|
| `tool` | `str` | Tool name |
| `total_tokens` | `int` | Cumulative tokens used so far this turn |
| `thinking_tokens` | `int` | Thinking tokens from the most recent API response |

**Stop**:

| Field | Type | Description |
|-------|------|-------------|
| `total_tokens` | `int` | Total tokens used this turn |
| `thinking_tokens` | `int` | Total thinking tokens this turn |
| `tool_calls` | `int` | Number of tool calls made this turn |

### ToolRecord

In-memory representation of a loaded tool (not persisted).

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Tool name (directory name) |
| `schema` | `dict` | Anthropic API tool definition (name, description, input_schema) |
| `fn` | `async callable` | The function to invoke (imported or generated) |
| `skill_md` | `str` | Raw SKILL.md content (injected into system prompt) |
| `requires_approval` | `bool` | Whether this tool appears in config.yaml approval list |

### MemoryEntry

A single line in `.memory/MEMORY.md`.

| Field | Type | Description |
|-------|------|-------------|
| `date` | `str` | ISO date (YYYY-MM-DD) |
| `content` | `str` | The fact stored |
| `reason` | `str` | Why the agent decided to store this |

**Format on disk**: `- {date}: {content} ({reason})`

## Relationships

```text
Agent
  ├── has one  → AnthropicProvider
  ├── has one  → EventBus
  │                └── has many → Listener callbacks
  ├── has many → ToolRecord (loaded at startup)
  ├── has one  → conversation_history: list[dict]
  │                (grows during session, includes raw_content with thinking blocks)
  └── uses     → approval_required: set[str]

AnthropicProvider
  └── returns  → ProviderResponse (per API call)

EventBus
  └── emits    → Event (SessionStart | PreToolUse | PostToolUse | Stop)

ToolRecord
  ├── loaded from → tools/{name}/SKILL.md + tools/{name}/tool.py
  └── approval configured by → tools/config.yaml
```

## Lifecycle

**Session lifecycle**:
1. `main.py` creates Agent, Provider, EventBus, registers Listeners
2. Agent loads CLAUDE.md, MEMORY.md, scans tools/ → emits SessionStart
3. REPL loop: user input → Agent.run() → tool dispatch loop → Stop
4. Ctrl+C or exit → session ends, no cleanup needed (files already flushed)

**Conversation history lifecycle**:
- Created empty at session start
- Grows with each user message and assistant turn (including raw_content)
- Tool results appended as `tool_result` messages
- Never compacted, never persisted
- Token count logged each turn for observability

**Memory entry lifecycle**:
- Created when agent calls `update_memory` tool
- Appended immediately to `.memory/MEMORY.md`
- Loaded (first 200 lines) on next session start
- Never deleted by the system (developer manages manually)
