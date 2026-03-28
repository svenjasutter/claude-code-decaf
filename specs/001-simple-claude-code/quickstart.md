# Quickstart: Claude Code Decaf

## Prerequisites

- Python 3.12+
- An Anthropic API key with access to extended thinking models

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

Optionally create a `CLAUDE.md` in the project root with project
knowledge the assistant should always have:

```markdown
# Project
- Python 3.12, use uv not pip
- Tests: pytest, run before every commit
```

## Run

```bash
python main.py
```

The assistant starts an interactive REPL. Type a request and press Enter.

```
> list the files in this directory
```

You will see:
1. A dimmed panel showing the model's thinking process
2. Tool calls and their results
3. The assistant's final response
4. Token usage (total and thinking)

## CLI flags

```bash
python main.py --model claude-sonnet-4-20250514 \
               --max-tokens 16000 \
               --thinking-budget 10000 \
               --max-tool-output 10000 \
               --tool-timeout 120
```

## Add a tool

Create a folder under `tools/` with a `SKILL.md`:

```bash
mkdir tools/my_tool
cat > tools/my_tool/SKILL.md << 'EOF'
# my_tool
Does something useful.
## Gotchas
- Watch out for X.
EOF
```

For a Python tool, add `tool.py`:

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

Restart the assistant. The tool is now available.

To require approval before the tool runs, add its name to
`tools/config.yaml`:

```yaml
approval_required:
  - write_file
  - run_bash
  - my_tool
```

## View logs

Session logs are written to `.logs/` as JSONL files:

```bash
cat .logs/2026-03-26T10-23-01.jsonl | python -m json.tool --json-lines
```

Each line is a JSON object with `ts`, `event`, and `data` fields.

## Exit

Press `Ctrl+C` or type `exit`.
