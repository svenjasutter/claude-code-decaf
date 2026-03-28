"""T102 — Unit tests for AnthropicProvider (providers/anthropic.py)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from providers.anthropic import AnthropicProvider, ProviderResponse, TokenUsage


def _mock_block(type_: str, **kwargs):
    b = MagicMock()
    b.type = type_
    for k, v in kwargs.items():
        setattr(b, k, v)
    return b


def _mock_api_response(blocks, input_tokens=100, output_tokens=50):
    resp = MagicMock()
    resp.content = blocks
    resp.usage = MagicMock(input_tokens=input_tokens, output_tokens=output_tokens)
    return resp


@patch("providers.anthropic.AsyncAnthropic")
async def test_send_calls_api_with_correct_params(mock_cls):
    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(
        return_value=_mock_api_response([_mock_block("text", text="hi")])
    )
    mock_cls.return_value = mock_client

    provider = AnthropicProvider(model="test-model", max_tokens=999,
                                 budget_tokens=500)
    await provider.send(
        messages=[{"role": "user", "content": "hello"}],
        tools=[{"name": "t"}],
        system_prompt="sys",
    )

    call_kwargs = mock_client.messages.create.call_args.kwargs
    assert call_kwargs["model"] == "test-model"
    assert call_kwargs["max_tokens"] == 999
    assert call_kwargs["thinking"] == {"type": "enabled", "budget_tokens": 500}
    assert call_kwargs["system"] == "sys"
    assert call_kwargs["tools"] == [{"name": "t"}]
    assert call_kwargs["messages"] == [{"role": "user", "content": "hello"}]


def test_map_response_text_only():
    provider = AnthropicProvider.__new__(AnthropicProvider)
    text_block = _mock_block("text", text="answer")
    resp = _mock_api_response([text_block])

    result = provider._map_response(resp)

    assert isinstance(result, ProviderResponse)
    assert result.thinking == ""
    assert len(result.content) == 1
    assert result.content[0].text == "answer"
    assert result.raw_content == [text_block]


def test_map_response_with_thinking():
    provider = AnthropicProvider.__new__(AnthropicProvider)
    thinking_block = _mock_block("thinking", thinking="let me think")
    text_block = _mock_block("text", text="answer")
    resp = _mock_api_response([thinking_block, text_block])

    result = provider._map_response(resp)

    assert result.thinking == "let me think"
    assert len(result.content) == 1  # thinking excluded from content
    assert result.content[0].text == "answer"
    assert len(result.raw_content) == 2  # both blocks preserved


def test_map_response_with_tool_use():
    provider = AnthropicProvider.__new__(AnthropicProvider)
    tool_block = _mock_block("tool_use", name="read_file",
                             input={"path": "x.py"}, id="t1")
    resp = _mock_api_response([tool_block])

    result = provider._map_response(resp)

    assert len(result.content) == 1
    assert result.content[0].type == "tool_use"
    assert result.content[0].name == "read_file"


def test_token_usage_populated():
    provider = AnthropicProvider.__new__(AnthropicProvider)
    resp = _mock_api_response([_mock_block("text", text="ok")],
                              input_tokens=150, output_tokens=75)

    result = provider._map_response(resp)

    assert result.usage.input_tokens == 150
    assert result.usage.output_tokens == 75
    assert result.usage.thinking_tokens == 0  # no thinking text


def test_thinking_tokens_estimated():
    provider = AnthropicProvider.__new__(AnthropicProvider)
    thinking_text = "a" * 400  # 400 chars / 4 ≈ 100 tokens
    resp = _mock_api_response([
        _mock_block("thinking", thinking=thinking_text),
        _mock_block("text", text="ok"),
    ])

    result = provider._map_response(resp)
    assert result.usage.thinking_tokens == 100


@patch("providers.anthropic.AsyncAnthropic")
async def test_send_propagates_api_exception(mock_cls):
    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(side_effect=RuntimeError("network"))
    mock_cls.return_value = mock_client

    provider = AnthropicProvider()
    with pytest.raises(RuntimeError, match="network"):
        await provider.send([], [], "")
