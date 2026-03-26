# Implementation Plan: Claude Code Decaf

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
├── test_agent.py            # Agent loop unit tests
├── test_events.py           # Event bus tests
├── test_loader.py           # Tool discovery tests
├── test_provider.py         # Provider response mapping tests
└── test_tools.py            # Individual tool function tests
```

**Structure Decision**: Single flat project at repository root. No `src/`
wrapper — every module is directly importable. Tools live under `tools/`
with one subdirectory per tool. Listeners are separated from the agent
loop for single-responsibility clarity. The `providers/` directory exists
for organisational clarity even though only one provider is in scope.

## Complexity Tracking

> No violations detected. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none)    |            |                                     |
