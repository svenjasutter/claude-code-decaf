# Claude Code Decaf

An educational re-implementation of Claude Code that makes the agent loop, memory system, and tool execution fully transparent and explainable.

Every design decision prioritises **explainability over completeness**. If a feature obscures how the agent works, it is out of scope.

## What you'll learn

- How an agentic coding assistant works under the hood
- The tool dispatch loop: model → tool calls → results → model
- CoALA memory architecture: semantic, episodic, working, procedural
- How ReAct (think → act → observe) drives the loop while CoALA organises the state it operates over
- Extended thinking: visible chain-of-thought reasoning
- Event-driven architecture with structured logging

## Architecture

```
main.py (CLI + REPL)
└── agent.py (agent loop)
    ├── providers/anthropic.py (API wrapper + extended thinking)
    ├── events.py (pub/sub event bus)
    │   └── listeners/
    │       ├── ui.py         (terminal rendering)
    │       ├── logging.py    (JSONL structured logs)
    │       └── approval.py   (human-in-the-loop)
    └── tools/
        ├── loader.py         (dynamic discovery)
        ├── read_file/        (Python tool)
        ├── write_file/       (Python tool)
        ├── find_files/       (Python tool)
        ├── list_directory/   (Python tool)
        ├── run_bash/         (Python tool)
        ├── update_memory/    (Python tool)
        └── prettier/         (CLI tool auto-wrapped)
```

8 core source files. No frameworks. No magic.

## Prerequisites

- Python 3.12+
- An Anthropic API key

## Install

```bash
git clone <repo-url> claude-code-decaf
cd claude-code-decaf
python -m venv .venv
source .venv/bin/activate
pip install anthropic rich aioconsole pyyaml
```

## Configure

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

Optionally create a `CLAUDE.md` in the project root with knowledge the assistant should always have:

```markdown
# Project
- Python 3.12, use uv not pip
- Tests: pytest, run before every commit
```

## Run

```bash
python main.py
```

```
> list the files in this directory
```

You will see:

1. A dimmed panel showing the model's thinking process
2. Tool calls and their results
3. The assistant's final response
4. Token usage (total and thinking)

## CLI flags

| Flag | Default | Description |
|------|---------|-------------|
| `--model` | `claude-sonnet-4-20250514` | Anthropic model to use |
| `--max-tokens` | `16000` | Max tokens per response |
| `--thinking-budget` | `10000` | Tokens reserved for thinking |
| `--max-tool-output` | `10000` | Max characters per tool result |
| `--tool-timeout` | `120` | Tool execution timeout (seconds) |

## Memory system

Based on the [CoALA cognitive architecture](https://arxiv.org/abs/2309.02427):

| Type | File | Author | Persists? |
|------|------|--------|-----------|
| Semantic | `CLAUDE.md` | Developer | Yes |
| Episodic | `.memory/MEMORY.md` | Agent | Yes |
| Working | Context window | Both | No |
| Procedural | `SKILL.md` + `tool.py` | Developer | Yes |

- **Working Memory** Because LLMs are stateless, conversation history must be maintained explicitly across decision cycles. The live context window serves this role, and token usage is logged each turn to keep it observable.
- **Procedural Memory** The agent's capabilities are extended through a tool system: modular tools (CLI-based or Python-based) the agent can discover and invoke at runtime. Each tool is defined by a schema (`tool.py`) and a usage guide (`SKILL.md`).
- **Semantic Memory** Project knowledge is written by the developer in `CLAUDE.md` and loaded at startup. In production systems this store is typically a vector database (e.g. ChromaDB), where RAG lets the agent retrieve only the most relevant chunks at query time without exceeding the context window. Here we load everything at startup, which is simpler but does not scale.
- **Episodic Memory** Facts and outcomes the agent learns during a session are persisted to `.memory/MEMORY.md` via `update_memory`. This file is loaded at the start of each new session, letting the agent build on past interactions over time.

## Add a tool

Create a folder under `tools/` with a `SKILL.md`:

```bash
mkdir tools/my_tool
```

**Python tool** add `SKILL.md` + `tool.py`:

```python
# tools/my_tool/tool.py
SCHEMA = {
    "name": "my_tool",
    "description": "Does something useful.",
    "input_schema": {
        "type": "object",
        "properties": {
            "arg": {"type": "string", "description": "An argument."}
        },
        "required": ["arg"]
    }
}

async def my_tool(arg: str) -> str:
    return f"Result for {arg}"
```

**CLI tool** add only `SKILL.md` (a subprocess wrapper is generated automatically).

To require approval before execution, add the tool name to `tools/config.yaml`:

```yaml
approval_required:
  - write_file
  - run_bash
  - my_tool
```

Restart the assistant. No existing files need editing.

## View logs

Session logs are written to `.logs/` as JSONL:

```bash
cat .logs/*.jsonl | python -m json.tool --json-lines
```

Each line is a JSON object with `ts`, `event`, and `data` fields:

```json
{"ts": "...", "event": "SessionStart",  "data": {"tools_loaded": [...], "claude_md_lines": 12}}
{"ts": "...", "event": "PreToolUse",    "data": {"tool": "read_file", "args": {"path": "auth.py"}}}
{"ts": "...", "event": "PostToolUse",   "data": {"tool": "read_file", "total_tokens": 3210}}
{"ts": "...", "event": "Stop",          "data": {"total_tokens": 4100, "thinking_tokens": 83, "tool_calls": 2}}
```

## How ReAct and CoALA fit together

**[CoALA](https://arxiv.org/abs/2309.02427)** organises *where* information lives (the four memory types above).  
**[ReAct](https://arxiv.org/pdf/2210.03629)** defines *how* the agent uses it: a repeating **Thought → Action → Observation** loop.

Each decision cycle:

1. **Thought** reason over working memory (which includes the loaded `CLAUDE.md` and `MEMORY.md`)
2. **Action** pick and execute a tool from procedural memory
3. **Observation** fold the result back into working memory, repeat or stop

After the loop ends, `update_memory` can persist what was learned to episodic memory for future sessions.

## Guidance files

| File | Purpose | CoALA type |
|------|---------|------------|
| `CLAUDE.md` | *What is this project?* structure, stack, conventions | Semantic (mostly) |
| `CONSTITUTION.md` | *How must we build it?* principles, rules, constraints | Procedural |

## Out of scope (by design)

| Feature | Why excluded |
|---------|-------------|
| Streaming | Adds async generator complexity before the basic loop is understood |
| Sub-agents | Adds a second loop before the first is understood |
| Vector retrieval | Adds infrastructure unrelated to the core loop |
| MCP servers | External protocol layer is out of scope |
| Context compaction | Production problem, not a learning problem |
| Auto memory | Implicit writes obscure the mechanism; `update_memory` is explicit |

## Token use observation (for spec-kit)

 npx ccusage@latest session
 claude-monitor
