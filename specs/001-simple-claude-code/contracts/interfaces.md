# Internal Interface Contracts

**Date**: 2026-03-26

This project has no external API. All interfaces are internal Python
contracts between modules. Documented here for implementation clarity.

## 1. Provider Interface

```python
class AnthropicProvider:
    async def send(
        self,
        messages: list[dict],
        tools: list[dict],
        system_prompt: str,
    ) -> ProviderResponse: ...
```

**Contract**:
- MUST enable extended thinking on every call
- MUST return a `ProviderResponse` with thinking text extracted, content
  blocks separated, and raw_content preserved for history
- MUST propagate API exceptions (no internal retry)

## 2. Event Bus Interface

```python
class EventBus:
    def subscribe(
        self,
        event_type: str,
        callback: Callable[[Event], Awaitable[None]],
    ) -> None: ...

    async def emit(self, event: Event) -> None: ...
```

**Contract**:
- `emit` calls all subscribers for the event type sequentially
  (order of subscription)
- Listener exceptions MUST NOT crash the agent loop (log and continue)
- All callbacks MUST be `async def`

## 3. Tool Function Interface

```python
# Python tool
async def tool_name(**kwargs) -> str: ...

# CLI tool (auto-generated)
async def tool_name(command: str) -> str: ...
```

**Contract**:
- MUST accept keyword arguments matching `input_schema.properties`
- MUST return a string (the tool result passed back to the model)
- MUST NOT block the event loop (use asyncio subprocess/file I/O)
- Output MUST be truncated by the agent loop to `--max-tool-output`
  characters before passing to the model

## 4. Tool Loader Interface

```python
def load_tools() -> tuple[
    list[dict],       # tool_definitions (API schemas)
    dict[str, Callable],  # tool_functions {name: async_fn}
    set[str],         # approval_required tool names
    list[str],        # skill_md_contents (for system prompt injection)
]: ...
```

**Contract**:
- Scans `tools/` for subdirectories containing `SKILL.md`
- For Python tools: imports `SCHEMA` and the named function from `tool.py`
- For CLI tools: generates schema from directory name + `SKILL.md` content,
  generates async subprocess wrapper
- CLI tool wrappers MUST bind loop variables explicitly (TC-001)
- Returns four parallel collections indexed by tool name

## 5. Agent Interface

```python
class Agent:
    async def run(self, user_input: str) -> str: ...
```

**Contract**:
- Appends user message to conversation history
- Calls provider in a loop until no tool_use blocks remain
- For each tool call:
  - Emits PreToolUse
  - Checks approval_required → awaits approval if needed
  - Executes tool function with `asyncio.wait_for(fn(), timeout)`
  - On timeout: returns error string as tool result
  - On denial: returns "Tool execution denied by user" as tool result
  - Emits PostToolUse
  - Appends tool_result to history
- Emits Stop when done
- Returns the final assistant text response

## 6. Approval Interface

```python
async def request_approval(tool_name: str, tool_input: dict) -> bool: ...
```

**Contract**:
- Displays tool name and arguments to the developer
- Prompts for y/n confirmation via async stdin
- Returns `True` (approved) or `False` (denied)
- MUST NOT block the event loop
