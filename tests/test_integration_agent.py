"""T106 — Integration tests for agent loop.

Mock only provider.send(); use real EventBus, real tool functions, real filesystem.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from agent import Agent
from events import EventBus
from providers.anthropic import ProviderResponse, TokenUsage
from tests.conftest import make_text_response, make_tool_use_response


# ── Helpers ──────────────────────────────────────────────────────────────


def _build_agent(send_sequence, *, tool_functions=None,
                 approval_required=None, approval_fn=None,
                 tool_timeout=120):
    """Build an agent with a real EventBus and the given provider responses."""
    provider = AsyncMock()
    provider.send = AsyncMock(side_effect=send_sequence)
    bus = EventBus()
    collected = []

    async def _collect(event):
        collected.append(event)

    for et in ("SessionStart", "Response", "PreToolUse", "PostToolUse", "Stop"):
        bus.subscribe(et, _collect)

    agent = Agent(
        provider=provider,
        event_bus=bus,
        tool_definitions=[],
        tool_functions=tool_functions or {},
        approval_required=approval_required or set(),
        system_prompt="integration test",
        tool_timeout=tool_timeout,
    )
    if approval_fn:
        agent.set_approval_fn(approval_fn)
    return agent, collected, provider


def _get_real_tools():
    """Load actual tool functions from the tools/ directory."""
    from tools.loader import load_tools
    _, fns, approval, _ = load_tools()
    return fns, approval


# ── AC-1, AC-3: text-only conversation e2e ───────────────────────────────


async def test_text_only_conversation_end_to_end():
    agent, events, _ = _build_agent([make_text_response("Hello world")])
    result = await agent.run("say hello")

    assert result == "Hello world"
    types = [e.event_type for e in events]
    assert "Response" in types
    assert "Stop" in types
    assert "PreToolUse" not in types


# ── AC-2: tool call with real list_directory ─────────────────────────────


async def test_tool_call_with_real_list_directory():
    fns, _ = _get_real_tools()
    responses = [
        make_tool_use_response("list_directory", {"path": "."}, "t1"),
        make_text_response("Here are the files."),
    ]
    agent, events, _ = _build_agent(responses, tool_functions=fns)
    result = await agent.run("list files")

    assert result == "Here are the files."
    # Verify list_directory actually ran and returned real results
    tool_result_msg = agent.conversation_history[2]
    tool_output = tool_result_msg["content"][0]["content"]
    assert "main.py" in tool_output or "agent.py" in tool_output


# ── AC-2: tool call with real read_file ──────────────────────────────────


async def test_tool_call_with_real_read_file():
    fns, _ = _get_real_tools()
    responses = [
        make_tool_use_response("read_file", {"path": "pyproject.toml"}, "t1"),
        make_text_response("Found it."),
    ]
    agent, events, _ = _build_agent(responses, tool_functions=fns)
    result = await agent.run("read pyproject")

    assert result == "Found it."
    tool_output = agent.conversation_history[2]["content"][0]["content"]
    assert "claude-code-decaf" in tool_output


# ── AC-2: multi-tool sequence ────────────────────────────────────────────


async def test_multi_tool_sequence_real_execution():
    fns, _ = _get_real_tools()
    responses = [
        make_tool_use_response("list_directory", {"path": "."}, "t1"),
        make_tool_use_response("read_file", {"path": "pyproject.toml"}, "t2"),
        make_text_response("All done."),
    ]
    agent, events, provider = _build_agent(responses, tool_functions=fns)
    result = await agent.run("list then read")

    assert result == "All done."
    assert provider.send.call_count == 3
    # Both tool results in history
    assert len(agent.conversation_history) == 6  # user, asst, tool, asst, tool, asst


# ── Edge: unknown tool recovery ──────────────────────────────────────────


async def test_unknown_tool_in_full_loop():
    responses = [
        make_tool_use_response("nonexistent_tool", {}, "t1"),
        make_text_response("I'll try another way."),
    ]
    agent, events, provider = _build_agent(responses)
    result = await agent.run("use unknown tool")

    assert result == "I'll try another way."
    assert provider.send.call_count == 2
    error_content = agent.conversation_history[2]["content"][0]["content"]
    assert "Unknown tool" in error_content


# ── Edge: approval denial ────────────────────────────────────────────────


async def test_denied_approval_in_full_loop():
    fns, _ = _get_real_tools()
    approval_fn = AsyncMock(return_value=False)
    responses = [
        make_tool_use_response("write_file", {"path": "/tmp/x", "content": "y"}, "t1"),
        make_text_response("Understood, skipping write."),
    ]
    agent, events, _ = _build_agent(
        responses,
        tool_functions=fns,
        approval_required={"write_file"},
        approval_fn=approval_fn,
    )
    result = await agent.run("write something")

    assert result == "Understood, skipping write."
    denial = agent.conversation_history[2]["content"][0]["content"]
    assert "denied" in denial.lower()


# ── Edge: tool timeout ──────────────────────────────────────────────────


async def test_tool_timeout_in_full_loop():
    async def sleeper(**kwargs):
        await asyncio.sleep(10)

    responses = [
        make_tool_use_response("sleeper", {}, "t1"),
        make_text_response("Timed out, moving on."),
    ]
    agent, events, _ = _build_agent(
        responses,
        tool_functions={"sleeper": sleeper},
        tool_timeout=0.05,
    )
    result = await agent.run("run sleeper")

    assert result == "Timed out, moving on."
    timeout_msg = agent.conversation_history[2]["content"][0]["content"]
    assert "timed out" in timeout_msg.lower()


# ── Edge: API error mid-conversation ─────────────────────────────────────


async def test_api_error_mid_conversation():
    fns, _ = _get_real_tools()
    responses = [
        make_tool_use_response("list_directory", {"path": "."}, "t1"),
        RuntimeError("server error 500"),
    ]
    provider = AsyncMock()
    call_count = 0

    async def send_side_effect(*args, **kwargs):
        nonlocal call_count
        r = responses[call_count]
        call_count += 1
        if isinstance(r, Exception):
            raise r
        return r

    provider.send = AsyncMock(side_effect=send_side_effect)
    bus = EventBus()
    collected = []

    async def _c(e):
        collected.append(e)
    for et in ("Response", "PreToolUse", "PostToolUse", "Stop"):
        bus.subscribe(et, _c)

    agent = Agent(provider=provider, event_bus=bus, tool_definitions=[],
                  tool_functions=fns, approval_required=set(),
                  system_prompt="test")
    result = await agent.run("list files")

    assert "server error 500" in result
    # History preserved up to failure point
    assert len(agent.conversation_history) >= 2  # user + assistant + tool_result at minimum


# ── Event sequence verification ──────────────────────────────────────────


async def test_event_sequence_integration():
    fns, _ = _get_real_tools()
    responses = [
        make_tool_use_response("list_directory", {"path": "."}, "t1"),
        make_text_response("Done."),
    ]
    agent, events, _ = _build_agent(responses, tool_functions=fns)
    await agent.run("list")

    types = [e.event_type for e in events]
    assert types == ["Response", "PreToolUse", "PostToolUse", "Response", "Stop"]


# ── Conversation history structure ───────────────────────────────────────


async def test_conversation_history_structure():
    fns, _ = _get_real_tools()
    responses = [
        make_tool_use_response("list_directory", {"path": "."}, "t1"),
        make_text_response("Here they are."),
    ]
    agent, events, _ = _build_agent(responses, tool_functions=fns)
    await agent.run("list")

    h = agent.conversation_history
    assert h[0]["role"] == "user"
    assert h[1]["role"] == "assistant"
    assert h[2]["role"] == "user"  # tool_result wrapped as user message
    assert h[2]["content"][0]["type"] == "tool_result"
    assert h[3]["role"] == "assistant"
