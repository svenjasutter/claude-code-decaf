# Research: Simple Claude Code

**Phase**: 0 — Outline & Research
**Date**: 2026-03-26

## Overview

No NEEDS CLARIFICATION items existed in the technical context. All
technology choices were specified in the feature description. This
document records the rationale for each decision.

## Decisions

### 1. Anthropic SDK (`anthropic` package)

**Decision**: Use `anthropic` Python SDK with `AsyncAnthropic` client.

**Rationale**: First-party SDK with native async support, typed
responses, and built-in extended thinking parameter. No wrapper needed.

**Alternatives considered**:
- Raw `httpx` calls: More control but duplicates SDK work (auth,
  retries, response parsing). Not simpler for an educational project.
- `litellm` multi-provider wrapper: Adds abstraction layer that
  obscures the Anthropic-specific thinking API. Violates Principle I
  (explainability) and introduces an unnecessary dependency.

### 2. Terminal UI (`rich`)

**Decision**: Use `rich` for terminal rendering (panels, markdown,
syntax highlighting).

**Rationale**: Widely adopted, well-documented, supports panels for
thinking blocks and markdown rendering for assistant output. No
curses-level complexity.

**Alternatives considered**:
- Plain `print()`: Functional but makes thinking blocks
  indistinguishable from output. Fails FR-009 (visually distinct).
- `textual` TUI framework: Full terminal app framework — far
  heavier than needed for a REPL. Violates Principle VI (minimalism).

### 3. Async stdin (`aioconsole`)

**Decision**: Use `aioconsole.ainput()` for non-blocking user input.

**Rationale**: Lightweight, single-purpose library. Keeps the REPL
and approval prompts non-blocking without manual thread pools.

**Alternatives considered**:
- `asyncio.to_thread(input)`: Works but wraps sync `input()` in a
  thread. Less explicit about the async nature. Acceptable fallback
  if `aioconsole` proves problematic.
- `prompt_toolkit`: Full readline-replacement with async support.
  Overkill for a simple `> ` prompt. Violates Principle VI.

### 4. YAML config (`pyyaml`)

**Decision**: Use `pyyaml` to parse `tools/config.yaml`.

**Rationale**: YAML is human-readable and already the standard for
tool configuration in the original Claude Code. `pyyaml` is the
de facto Python YAML library.

**Alternatives considered**:
- TOML (`tomllib`): Built into Python 3.11+ but less common for
  simple list-of-names config. No strong advantage.
- JSON: Noisier for a short list of tool names. YAML wins on
  readability for this use case.

### 5. Event bus pattern (custom, no library)

**Decision**: Implement a minimal pub/sub event bus in `events.py`
(~30 lines). No external library.

**Rationale**: The bus needs only `subscribe(event_type, callback)`
and `emit(event)`. Any library adds more API surface than the
implementation itself. A custom bus is more educational — the
developer reads the full implementation.

**Alternatives considered**:
- `blinker`: Mature signal library, but overkill for 4 event types.
- `pyee`: EventEmitter pattern. Adds a dependency for something
  trivially implementable. Violates Principle VI.

### 6. Tool discovery via filesystem scan

**Decision**: Scan `tools/` subdirectories for `SKILL.md` at startup.
Import `tool.py` if present, otherwise generate CLI wrapper.

**Rationale**: Filesystem convention is the simplest discovery
mechanism. No decorators, no entry points, no registration. Drop
a folder, restart, done.

**Alternatives considered**:
- Python entry points (`pkg_resources`): Requires packaging setup.
  Too heavyweight for a flat project.
- Decorator registry (`@register_tool`): Requires importing modules
  to trigger registration. Less explicit than filesystem scan.

### 7. No retry on API errors

**Decision**: Surface API errors immediately, return to REPL.
No retry logic.

**Rationale**: Retry with backoff adds 20+ lines of logic
(exponential backoff, jitter, max attempts) for a case that rarely
occurs in educational single-user usage. The developer can simply
press Enter to retry. Aligns with Principle VI (simplicity).

### 8. Tool timeout via asyncio.wait_for

**Decision**: Wrap tool execution in `asyncio.wait_for(fn(), timeout)`
with a default of 120 seconds.

**Rationale**: Built-in asyncio mechanism. On timeout, raises
`asyncio.TimeoutError`, which the agent loop catches and converts
to a tool error result. No external dependency needed.
