"""Terminal UI listener — renders thinking, text, tool calls, and token usage."""

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from events import Event, EventBus

console = Console()


def register_ui_listener(event_bus: EventBus):
    event_bus.subscribe("Response", _on_response)
    event_bus.subscribe("PreToolUse", _on_pre_tool_use)
    event_bus.subscribe("PostToolUse", _on_post_tool_use)
    event_bus.subscribe("Stop", _on_stop)
    event_bus.subscribe("SessionStart", _on_session_start)


async def _on_session_start(event: Event):
    data = event.data
    console.print(Panel(
        f"Tools: {', '.join(data.get('tools_loaded', []))}\n"
        f"CLAUDE.md: {data.get('claude_md_lines', 0)} lines\n"
        f"MEMORY.md: {data.get('memory_md_lines', 0)} lines",
        title="Session Started",
        style="bold green",
    ))


async def _on_response(event: Event):
    data = event.data
    thinking = data.get("thinking", "")
    content = data.get("content", [])
    usage = data.get("usage")

    # Render thinking in a dimmed panel
    if thinking:
        console.print(Panel(
            thinking,
            title="Thinking",
            style="dim",
            border_style="dim",
        ))

    # Render text blocks
    for block in content:
        if block.type == "text":
            console.print(Markdown(block.text))

    # Show token usage
    if usage:
        total = usage.input_tokens + usage.output_tokens
        console.print(
            f"  [dim]tokens: {total} total, {usage.thinking_tokens} thinking[/dim]"
        )


async def _on_pre_tool_use(event: Event):
    data = event.data
    tool = data.get("tool", "unknown")
    args = data.get("args", {})
    # Show a compact summary of the args
    args_str = ", ".join(f"{k}={repr(v)[:60]}" for k, v in args.items())
    console.print(f"  [bold yellow]▶ {tool}[/bold yellow]({args_str})")


async def _on_post_tool_use(event: Event):
    data = event.data
    tool = data.get("tool", "unknown")
    console.print(f"  [green]✓ {tool}[/green] done")


async def _on_stop(event: Event):
    data = event.data
    total = data.get("total_tokens", 0)
    thinking = data.get("thinking_tokens", 0)
    calls = data.get("tool_calls", 0)
    error = data.get("error")
    if error:
        console.print(f"  [red]Error: {error}[/red]")
    console.print(
        f"  [dim]Turn complete: {total} tokens, "
        f"{thinking} thinking, {calls} tool calls[/dim]"
    )
