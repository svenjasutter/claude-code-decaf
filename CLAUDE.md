# claude-code-decaf Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-26

## Active Technologies

- Python 3.12+ + anthropic, rich, aioconsole, pyyaml (001-simple-claude-code)

## Project Structure

```text
main.py              # CLI entry point, async REPL
agent.py             # Agent loop, conversation history
events.py            # Event bus (pub/sub)
providers/
  anthropic.py       # AsyncAnthropic wrapper
listeners/
  ui.py              # Terminal UI (rich)
  logging.py         # JSON structured logging
  approval.py        # Human-in-the-loop approval
tools/
  loader.py          # Dynamic tool discovery
  config.yaml        # Approval policy
  <tool_name>/       # One folder per tool (SKILL.md + optional tool.py)
tests/
```

## Commands

```bash
python main.py                    # Run the assistant
pytest                            # Run tests
ruff check .                      # Lint
```

## Code Style

Python 3.12+: Follow standard conventions. All I/O functions must be async def.

## Recent Changes

- 001-simple-claude-code: Initial feature — agent loop, memory, tools, events

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
