"""CLI entry point — async REPL, argument parsing, session startup."""

import argparse
import asyncio
import os
import sys
from pathlib import Path

from aioconsole import ainput

from agent import Agent
from events import Event, EventBus
from providers.anthropic import AnthropicProvider
from tools.loader import load_tools
from listeners.ui import register_ui_listener
from listeners.approval import request_approval
from listeners.logging import register_logging_listener


def build_system_prompt(skill_md_contents: list[str],
                        claude_md: str, memory_md: str) -> str:
    parts = []
    parts.append("You are a helpful coding assistant.")

    if claude_md:
        parts.append(f"\n## Project Knowledge (CLAUDE.md)\n\n{claude_md}")

    if memory_md:
        parts.append(f"\n## Learned Facts (MEMORY.md)\n\n{memory_md}")

    if skill_md_contents:
        parts.append("\n## Tool Usage Guides\n")
        for md in skill_md_contents:
            parts.append(md)

    return "\n".join(parts)


def load_memory_files() -> tuple[str, int, str, int]:
    claude_md = ""
    claude_md_lines = 0
    memory_md = ""
    memory_md_lines = 0

    claude_path = Path("CLAUDE.md")
    if claude_path.exists():
        claude_md = claude_path.read_text()
        claude_md_lines = len(claude_md.splitlines())

    memory_path = Path(".memory/MEMORY.md")
    if memory_path.exists():
        lines = memory_path.read_text().splitlines()
        memory_md_lines = len(lines)
        memory_md = "\n".join(lines[:200])

    return claude_md, claude_md_lines, memory_md, memory_md_lines


async def main():
    parser = argparse.ArgumentParser(description="Claude Code Decaf")
    parser.add_argument("--model", default="claude-sonnet-4-20250514")
    parser.add_argument("--max-tokens", type=int, default=16000)
    parser.add_argument("--thinking-budget", type=int, default=10000)
    parser.add_argument("--max-tool-output", type=int, default=10000)
    parser.add_argument("--tool-timeout", type=int, default=120)
    args = parser.parse_args()

    # Validate API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable is not set.")
        sys.exit(1)

    # Load memory
    claude_md, claude_md_lines, memory_md, memory_md_lines = load_memory_files()

    # Load tools
    tool_definitions, tool_functions, approval_required, skill_md_contents = load_tools()
    tool_names = [t["name"] for t in tool_definitions]

    # Build system prompt
    system_prompt = build_system_prompt(skill_md_contents, claude_md, memory_md)

    # Create provider and event bus
    provider = AnthropicProvider(
        model=args.model,
        max_tokens=args.max_tokens,
        budget_tokens=args.thinking_budget,
    )
    event_bus = EventBus()

    # Register listeners
    register_ui_listener(event_bus)
    register_logging_listener(event_bus)

    # Create agent
    agent = Agent(
        provider=provider,
        event_bus=event_bus,
        tool_definitions=tool_definitions,
        tool_functions=tool_functions,
        approval_required=approval_required,
        system_prompt=system_prompt,
        tool_timeout=args.tool_timeout,
        max_tool_output=args.max_tool_output,
    )
    agent.set_approval_fn(request_approval)

    # Emit SessionStart
    await event_bus.emit(Event("SessionStart", {
        "claude_md_lines": claude_md_lines,
        "memory_md_lines": memory_md_lines,
        "tools_loaded": tool_names,
        "tokens_used": len(system_prompt),
    }))

    # REPL loop
    while True:
        try:
            user_input = await ainput("> ")
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        user_input = user_input.strip()
        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            print("Goodbye!")
            break

        await agent.run(user_input)


if __name__ == "__main__":
    asyncio.run(main())
