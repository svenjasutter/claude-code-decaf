# Spec Driven Development — Process Summary

> Building a minimal, educational agentic coding assistant ("Simple Claude Code") using Spec Driven Development with [Speckit](https://github.com/speckit) and Claude Code.

---

## What is Spec Driven Development?

Spec Driven Development (SDD) is a workflow where you write structured specifications *before* writing code. An AI agent (Claude Code + Speckit) then generates design artifacts, implementation plans, and task breakdowns from those specs — and ultimately implements the code itself.

The pipeline: **Spec → Constitution → Clarify → Plan → Tasks → Implement → Test**

---

## The Project

An educational re-implementation of Claude Code that makes the agent loop, memory system (CoALA architecture), and tool execution fully transparent and explainable.

**Key architectural decisions:**
- Async-first (full asyncio stack)
- Dynamic tool discovery (add a file, never edit existing ones)
- CoALA memory: semantic (`CLAUDE.md`), episodic (`MEMORY.md`), working (context window), procedural (`SKILL.md` + tools)
- Extended thinking visible to the developer
- Event bus with listeners (UI, logging, approval)

---

## Step-by-Step Process

### 1. Initialize Speckit

```bash
specify init . --ai claude
```

This sets up the `.specify/` directory in your project and connects Speckit to Claude Code as the AI backend.

### 2. Set the Constitution

```
/speckit.constitution This project is a minimal, educational agentic coding
assistant. All design decisions must prioritise explainability over completeness.
The full stack is async (asyncio). Tools are discovered dynamically — adding a
tool never requires editing existing files. Memory follows the CoALA architecture
(semantic, episodic, working, procedural). Extended thinking must be enabled on
every API call and thinking blocks must be visible to the developer. No streaming,
no subagents, no vector retrieval, no MCP servers — these are explicitly out of scope.
```

The constitution acts as a guardrail. Every subsequent step (plan, tasks, implementation) is checked against these 6 core principles:

1. Explainability Over Completeness
2. Async-First
3. Dynamic Tool Discovery
4. CoALA Memory Architecture
5. Visible Extended Thinking
6. Simplicity and Minimalism

### 3. Specify — Generate the Spec

```
/speckit.specify myspecs.md
```

Speckit reads your input spec (user stories, acceptance criteria, requirements) and generates a structured technical specification. It flags areas that need clarification.

![After /speckit.specify — generated spec with clarification flags](assets/Pasted%20image%2020260326223052.png)

*Brewed for 2m 35s. Cost at this point: ~$0.98 / 816K tokens.*

### 4. Clarify — Refine the Spec

Read through the generated `spec.md`, identify gaps, then run:

```
/speckit.clarify
```

This is an interactive step where you tell Claude what to refine. The spec evolves through conversation — you provide the domain knowledge, Claude structures it.

### 5. Plan — Generate Design Artifacts

```
/speckit.plan
```

Speckit generates a full set of implementation artifacts and validates them against the constitution.

![Plan complete — generated artifacts with constitution check](assets/Pasted%20image%2020260326225611.png)

**Generated artifacts:**

| Artifact | Path |
|---|---|
| Implementation Plan | `specs/001-simple-claude-code/plan.md` |
| Research | `specs/001-simple-claude-code/research.md` |
| Data Model | `specs/001-simple-claude-code/data-model.md` |
| Quickstart | `specs/001-simple-claude-code/quickstart.md` |
| Interface Contracts | `specs/001-simple-claude-code/contracts/interfaces.md` |
| Agent Context | `CLAUDE.md` (updated) |

*Constitution check: ALL PASS (pre-design and post-design). Brewed for 3m 13s.*

### 6. Tasks — Break Down the Work

```
/speckit.tasks
```

Generates an ordered, dependency-aware task list from the plan. Each task is scoped to be individually implementable.

*Cost at this point: ~$3.98 / 5.7M tokens.*

### 7. Implement — Execute the Tasks

```
/speckit.implement
```

Claude implements all tasks across 8 phases, writing the actual code files.

![Implementation complete — 35 tasks across 8 phases](assets/Pasted%20image%2020260326232756.png)

**Result:**
- 35/35 tasks completed across 8 phases (Foundations, CLI/REPL, Event Bus, Provider, Memory, Tool Discovery, Agent Loop, Polish)
- 9 core files generated (`main.py`, `agent.py`, `events.py`, `providers/anthropic.py`, etc.)
- 7 tools implemented (`read_file`, `write_file`, `find_files`, `list_directory`, `run_bash`, `update_memory`, `prettier`)
- All files follow the constitution (async, dynamic discovery, CoALA memory)

### 8. Test — Add a Testing Phase

```
/speckit.plan Add a testing phase for User Story 1. US1 implementation
is already complete. Plan unit tests and integration tests that cover
all US1 acceptance criteria.
```

You can re-enter the plan step to add testing or new features on top of the existing implementation.

---

## Cost & Token Summary

| Phase | Total Tokens | Cost (USD) |
|---|---|---|
| Specify + Clarify | ~816K | $0.98 |
| Plan | ~4.7M | $3.30 |
| Tasks | ~5.7M | $3.98 |
| Implement (mid) | ~8.9M | $6.39 |
| Implement (final) | ~11.4M | $8.41 |

**Total cost for full spec-to-implementation: ~$8.41** using Claude Opus 4.6.

---

## Key Learnings

1. **The spec is the product** — the better your input spec, the better every downstream artifact. Time spent on specification is never wasted.
2. **Constitution as guardrails** — defining principles upfront prevents scope creep. Every plan and task is validated against the constitution.
3. **Start minimal** — begin with only the functionality needed for the program to work, then iterate. Speckit reminds you when you miss a step.
4. **Three-artifact pipeline** — `spec.md` (what users need) → `plan.md` (how to build it) → `tasks.md` (what steps in what order). Each artifact has a distinct purpose.
5. **Be specific** — vague specs produce vague code. The clarify step exists for a reason.
6. **Protect your files** — make sure generated files don't get overwritten between iterations.

---

## Speckit Commands Reference

| Command | Purpose |
|---|---|
| `/speckit.plan` | Generate implementation plan from design artifacts |
| `/speckit.tasks` | Generate dependency-ordered task list |
| `/speckit.implement` | Execute all tasks defined in tasks.md |
| `/speckit.clarify` | Identify gaps and resolve ambiguities in the spec |
| `/speckit.specify` | Parse and validate a specification file |
| `/speckit.verify` | Run constitution and quality checks |
| `/speckit.constitution` | Define project principles and constraints |

![Speckit commands in Claude Code](assets/Pasted%20image%2020260328133346.png)
