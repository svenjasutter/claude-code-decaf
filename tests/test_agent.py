"""T103 — Unit tests for Agent class (agent.py)."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from agent import Agent
from events import EventBus
from tests.conftest import (
    make_text_response,
    make_tool_use_response,
    make_thinking_response,
)


def _make_agent(provider_send_side_effect, *,
                tool_functions=None, approval_required=None,
                approval_fn=None, tool_timeout=120,
                max_tool_output=10000):
    """Helper to build an Agent with a mocked provider."""
    provider = AsyncMock()
    provider.send = AsyncMock(side_effect=provider_send_side_effect)

    bus = EventBus()
    collected = []

    async def _collect(event):
        collected.append(event)

    for etype in ("SessionStart", "Response", "PreToolUse", "PostToolUse", "Stop"):
        bus.subscribe(etype, _collect)

    agent = Agent(
        provider=provider,
        event_bus=bus,
        tool_definitions=[],
        tool_functions=tool_functions or {},
        approval_required=approval_required or set(),
        system_prompt="test",
        tool_timeout=tool_timeout,
        max_tool_output=max_tool_output,
    )
    if approval_fn is not None:
        agent.set_approval_fn(approval_fn)
    return agent, collected, provider


# ── AC-1 / AC-3: text-only response ──────────────────────────────────────


async def test_text_only_response():
    agent, events, _ = _make_agent([make_text_response("Hello!")])
    result = await agent.run("hi")

    assert result == "Hello!"
    assert agent.conversation_history[0] == {"role": "user", "content": "hi"}
    assert agent.conversation_history[1]["role"] == "assistant"
    # Stop event emitted
    stop_events = [e for e in events if e.event_type == "Stop"]
    assert len(stop_events) == 1
    assert stop_events[0].data["tool_calls"] == 0


# ── AC-2: single tool call then text ─────────────────────────────────────


async def test_single_tool_call_then_text():
    tool_fn = AsyncMock(return_value="file contents")
    responses = [
        make_tool_use_response("read_file", {"path": "x.py"}, "t1"),
        make_text_response("Here is the file."),
    ]
    agent, events, _ = _make_agent(responses,
                                   tool_functions={"read_file": tool_fn})
    result = await agent.run("read x.py")

    assert result == "Here is the file."
    tool_fn.assert_called_once_with(path="x.py")
    # Verify event sequence: Response, PreToolUse, PostToolUse, Response, Stop
    types = [e.event_type for e in events]
    assert types == ["Response", "PreToolUse", "PostToolUse", "Response", "Stop"]


# ── AC-2: multiple tool calls in one response ────────────────────────────


async def test_multiple_tool_calls_in_one_response():
    from tests.conftest import _make_block
    fn_a = AsyncMock(return_value="result_a")
    fn_b = AsyncMock(return_value="result_b")

    # Build a response with two tool_use blocks
    block_a = _make_block("tool_use", name="a", input={}, id="t1")
    block_b = _make_block("tool_use", name="b", input={}, id="t2")
    from providers.anthropic import ProviderResponse, TokenUsage
    multi_tool_resp = ProviderResponse(
        thinking="", content=[block_a, block_b],
        raw_content=[block_a, block_b],
        usage=TokenUsage(10, 20, 0),
    )

    responses = [multi_tool_resp, make_text_response("done")]
    agent, events, _ = _make_agent(responses,
                                   tool_functions={"a": fn_a, "b": fn_b})
    result = await agent.run("do both")

    assert result == "done"
    fn_a.assert_called_once()
    fn_b.assert_called_once()


async def test_multi_turn_tool_loop():
    fn = AsyncMock(return_value="ok")
    responses = [
        make_tool_use_response("t", {}, "t1"),
        make_tool_use_response("t", {}, "t2"),
        make_tool_use_response("t", {}, "t3"),
        make_text_response("final"),
    ]
    agent, events, provider = _make_agent(responses,
                                          tool_functions={"t": fn})
    result = await agent.run("loop")

    assert result == "final"
    assert fn.call_count == 3
    assert provider.send.call_count == 4


# ── Edge: unknown tool ───────────────────────────────────────────────────


async def test_unknown_tool_returns_error():
    responses = [
        make_tool_use_response("nonexistent", {}, "t1"),
        make_text_response("ok"),
    ]
    agent, events, _ = _make_agent(responses)
    result = await agent.run("call unknown")

    assert result == "ok"
    # Tool result in history should contain error
    tool_result_msg = agent.conversation_history[2]  # user msg with tool_results
    assert "Unknown tool" in tool_result_msg["content"][0]["content"]


# ── Edge: tool execution failure ─────────────────────────────────────────


async def test_tool_execution_failure():
    fn = AsyncMock(side_effect=RuntimeError("disk full"))
    responses = [
        make_tool_use_response("write_file", {"path": "x"}, "t1"),
        make_text_response("ok"),
    ]
    agent, events, _ = _make_agent(responses,
                                   tool_functions={"write_file": fn})
    result = await agent.run("write")

    assert result == "ok"
    tool_result = agent.conversation_history[2]["content"][0]["content"]
    assert "disk full" in tool_result


# ── Edge: approval denied ────────────────────────────────────────────────


async def test_tool_approval_denied():
    fn = AsyncMock(return_value="should not run")
    approval = AsyncMock(return_value=False)
    responses = [
        make_tool_use_response("write_file", {"path": "x"}, "t1"),
        make_text_response("ok"),
    ]
    agent, events, _ = _make_agent(
        responses,
        tool_functions={"write_file": fn},
        approval_required={"write_file"},
        approval_fn=approval,
    )
    result = await agent.run("write")

    assert result == "ok"
    fn.assert_not_called()
    tool_result = agent.conversation_history[2]["content"][0]["content"]
    assert "denied" in tool_result.lower()


async def test_tool_approval_approved():
    fn = AsyncMock(return_value="written")
    approval = AsyncMock(return_value=True)
    responses = [
        make_tool_use_response("write_file", {"path": "x"}, "t1"),
        make_text_response("ok"),
    ]
    agent, events, _ = _make_agent(
        responses,
        tool_functions={"write_file": fn},
        approval_required={"write_file"},
        approval_fn=approval,
    )
    await agent.run("write")
    fn.assert_called_once()


# ── Edge: tool timeout ──────────────────────────────────────────────────


async def test_tool_timeout():
    async def slow(**kwargs):
        await asyncio.sleep(10)

    responses = [
        make_tool_use_response("slow_tool", {}, "t1"),
        make_text_response("ok"),
    ]
    agent, events, _ = _make_agent(
        responses,
        tool_functions={"slow_tool": slow},
        tool_timeout=0.05,
    )
    result = await agent.run("go")

    assert result == "ok"
    tool_result = agent.conversation_history[2]["content"][0]["content"]
    assert "timed out" in tool_result.lower()


# ── Edge: tool output truncation ─────────────────────────────────────────


async def test_tool_output_truncation():
    fn = AsyncMock(return_value="x" * 200)
    responses = [
        make_tool_use_response("big", {}, "t1"),
        make_text_response("ok"),
    ]
    agent, events, _ = _make_agent(
        responses,
        tool_functions={"big": fn},
        max_tool_output=50,
    )
    await agent.run("go")

    tool_result = agent.conversation_history[2]["content"][0]["content"]
    assert len(tool_result) <= 50 + len("\n... (truncated)")
    assert "truncated" in tool_result


# ── Edge: API error ──────────────────────────────────────────────────────


async def test_api_error_returns_to_repl():
    provider = AsyncMock()
    provider.send = AsyncMock(side_effect=RuntimeError("rate limit"))
    bus = EventBus()
    collected = []

    async def _c(e):
        collected.append(e)
    for et in ("Response", "PreToolUse", "PostToolUse", "Stop"):
        bus.subscribe(et, _c)

    agent = Agent(provider=provider, event_bus=bus, tool_definitions=[],
                  tool_functions={}, approval_required=set(),
                  system_prompt="test")
    result = await agent.run("hello")

    assert "rate limit" in result
    # History preserved (user message still there)
    assert len(agent.conversation_history) == 1
    assert agent.conversation_history[0]["content"] == "hello"
    # Stop event emitted with error
    stops = [e for e in collected if e.event_type == "Stop"]
    assert len(stops) == 1
    assert "rate limit" in stops[0].data["error"]


# ── Event ordering ───────────────────────────────────────────────────────


async def test_events_emitted_in_order():
    fn = AsyncMock(return_value="ok")
    responses = [
        make_tool_use_response("t", {}, "t1"),
        make_text_response("done"),
    ]
    agent, events, _ = _make_agent(responses, tool_functions={"t": fn})
    await agent.run("go")

    types = [e.event_type for e in events]
    assert types == ["Response", "PreToolUse", "PostToolUse", "Response", "Stop"]


# ── Conversation history preservation ────────────────────────────────────


async def test_conversation_history_preserved_across_calls():
    agent, _, _ = _make_agent([
        make_text_response("first"),
        make_text_response("second"),
    ])
    await agent.run("q1")
    await agent.run("q2")

    assert len(agent.conversation_history) == 4  # user, asst, user, asst
    assert agent.conversation_history[0]["content"] == "q1"
    assert agent.conversation_history[2]["content"] == "q2"


# ── TC-002: raw_content in history ───────────────────────────────────────


async def test_raw_content_in_history():
    resp = make_thinking_response("hmm", "answer")
    agent, _, _ = _make_agent([resp])
    await agent.run("think")

    assistant_turn = agent.conversation_history[1]
    assert assistant_turn["role"] == "assistant"
    # raw_content has both thinking and text blocks
    assert len(assistant_turn["content"]) == 2
    assert assistant_turn["content"][0].type == "thinking"
    assert assistant_turn["content"][1].type == "text"
