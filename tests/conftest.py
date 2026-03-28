"""Shared fixtures for US1 tests."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from events import EventBus
from providers.anthropic import ProviderResponse, TokenUsage

# Ensure project root is on sys.path so bare imports (agent, events, …) resolve.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ── Mock content-block helpers ──────────────────────────────────────────────


def _make_block(type_: str, **kwargs):
    """Create a MagicMock that mimics an Anthropic SDK content block."""
    block = MagicMock()
    block.type = type_
    for k, v in kwargs.items():
        setattr(block, k, v)
    return block


def make_text_response(text: str, *, input_tokens: int = 10,
                       output_tokens: int = 20) -> ProviderResponse:
    """Build a ProviderResponse containing only a text block."""
    text_block = _make_block("text", text=text)
    return ProviderResponse(
        thinking="",
        content=[text_block],
        raw_content=[text_block],
        usage=TokenUsage(input_tokens=input_tokens,
                         output_tokens=output_tokens,
                         thinking_tokens=0),
    )


def make_tool_use_response(tool_name: str, tool_input: dict,
                           tool_use_id: str = "toolu_01",
                           *, input_tokens: int = 10,
                           output_tokens: int = 20) -> ProviderResponse:
    """Build a ProviderResponse containing a single tool_use block."""
    tool_block = _make_block("tool_use", name=tool_name,
                             input=tool_input, id=tool_use_id)
    return ProviderResponse(
        thinking="",
        content=[tool_block],
        raw_content=[tool_block],
        usage=TokenUsage(input_tokens=input_tokens,
                         output_tokens=output_tokens,
                         thinking_tokens=0),
    )


def make_thinking_response(thinking: str, text: str,
                           *, input_tokens: int = 10,
                           output_tokens: int = 20) -> ProviderResponse:
    """Build a ProviderResponse with a thinking block + text block."""
    thinking_block = _make_block("thinking", thinking=thinking)
    text_block = _make_block("text", text=text)
    return ProviderResponse(
        thinking=thinking,
        content=[text_block],
        raw_content=[thinking_block, text_block],
        usage=TokenUsage(input_tokens=input_tokens,
                         output_tokens=output_tokens,
                         thinking_tokens=len(thinking) // 4),
    )


# ── Event collector fixture ─────────────────────────────────────────────────


@pytest.fixture
def event_bus():
    return EventBus()


@pytest.fixture
def event_collector(event_bus):
    """Subscribe to all known event types and collect emitted events."""
    collected: list = []

    async def _collect(event):
        collected.append(event)

    for etype in ("SessionStart", "Response", "PreToolUse", "PostToolUse", "Stop"):
        event_bus.subscribe(etype, _collect)

    return collected
