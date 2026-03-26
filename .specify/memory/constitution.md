<!--
  === Sync Impact Report ===
  Version change: (new) → 1.0.0
  Modified principles: N/A (initial constitution)
  Added sections:
    - Core Principles (6 principles)
    - Explicit Exclusions
    - Development Workflow
    - Governance
  Removed sections: N/A
  Templates requiring updates:
    - .specify/templates/plan-template.md ⚠ pending
      (Constitution Check section must be populated per-feature
       against these principles)
    - .specify/templates/spec-template.md ✅ no changes needed
    - .specify/templates/tasks-template.md ✅ no changes needed
  Follow-up TODOs: None
-->

# Decaf Constitution

## Core Principles

### I. Explainability Over Completeness

Every design decision MUST prioritise clarity and learnability over
feature completeness. Code MUST be readable by a developer who has
never seen the project before. When a trade-off exists between a
more capable but opaque implementation and a simpler but transparent
one, the simpler option MUST be chosen.

**Rationale**: This is an educational project. If the code cannot
teach, it has failed its primary purpose.

### II. Async-First

The entire runtime stack MUST use Python `asyncio`. All I/O-bound
operations (API calls, file access, user interaction) MUST be
implemented as coroutines. Synchronous blocking calls inside the
event loop are prohibited.

**Rationale**: A consistent async model eliminates mixed-paradigm
confusion and reflects real-world agentic system design.

### III. Dynamic Tool Discovery

Tools MUST be discovered at runtime via a registry or convention
(e.g., directory scan, decorator, entry point). Adding a new tool
MUST NOT require editing any existing file — only adding a new
module or file. The tool loading mechanism MUST be explicit and
inspectable (no hidden magic).

**Rationale**: Open-closed design keeps the tool surface extensible
without destabilising existing behaviour.

### IV. CoALA Memory Architecture

Memory MUST be organised into four explicit stores following the
CoALA framework:

- **Semantic memory**: long-term factual knowledge (persisted)
- **Episodic memory**: past interaction traces (persisted)
- **Working memory**: current-turn scratchpad (ephemeral)
- **Procedural memory**: action repertoire / tool definitions

Each store MUST be a distinct, named component. Implementations
MUST NOT conflate stores or silently merge their contents.

**Rationale**: Explicit memory separation makes the agent's
reasoning observable and debuggable.

### V. Visible Extended Thinking

Extended thinking MUST be enabled on every Anthropic API call.
Thinking blocks returned by the model MUST be captured and
surfaced to the developer in a readable form (e.g., logged to
console or stored in working memory). Thinking content MUST
NOT be silently discarded.

**Rationale**: Thinking traces are the primary debugging and
learning tool for an educational agent.

### VI. Simplicity and Minimalism

The codebase MUST remain minimal. No feature is added unless it
directly serves the educational or functional goals stated above.
When in doubt, leave it out. Abstractions MUST justify their
existence by reducing complexity, not by anticipating future needs.

**Rationale**: A small codebase is a teachable codebase.

## Explicit Exclusions

The following capabilities are permanently out of scope. Any PR or
design document that introduces them MUST be rejected:

- **Streaming responses** — all API calls use non-streaming mode.
- **Sub-agents / multi-agent orchestration** — one agent, one loop.
- **Vector retrieval / embeddings search** — memory uses simple
  key-value or file-based storage only.
- **MCP servers** — no Model Context Protocol integrations.

If a future requirement appears to need one of these, the
constitution MUST be amended first (see Governance).

## Development Workflow

- All code changes MUST pass linting and type-checking before merge.
- New tools MUST include at least one usage example or test
  demonstrating their integration via the dynamic discovery path.
- Memory store changes MUST document which CoALA category is
  affected and why.
- API integration changes MUST confirm that extended thinking
  remains enabled and visible after the change.

## Governance

This constitution is the highest-authority document for the project.
It supersedes all other practices, templates, and ad-hoc decisions.

**Amendment procedure**:

1. Propose the change in a dedicated PR with a rationale.
2. Update this file with the new or revised text.
3. Increment the version per semantic versioning rules:
   - MAJOR: principle removal or incompatible redefinition.
   - MINOR: new principle or materially expanded guidance.
   - PATCH: clarifications, typo fixes, non-semantic refinements.
4. Update `LAST_AMENDED_DATE` to the merge date.
5. Run the consistency propagation checklist against all templates.

**Compliance review**: Every PR and design review MUST verify that
the proposed work does not violate any principle or introduce an
excluded capability. The plan template's "Constitution Check"
section MUST reference the specific principles validated.

**Version**: 1.0.0 | **Ratified**: 2026-03-26 | **Last Amended**: 2026-03-26
