"""Thin async wrapper around the Anthropic API with extended thinking."""

from dataclasses import dataclass
from anthropic import AsyncAnthropic


@dataclass
class TokenUsage:
    input_tokens: int
    output_tokens: int
    thinking_tokens: int


@dataclass
class ProviderResponse:
    thinking: str
    content: list
    raw_content: list
    usage: TokenUsage


class AnthropicProvider:
    def __init__(self, model: str = "claude-sonnet-4-20250514",
                 max_tokens: int = 16000, budget_tokens: int = 10000):
        self.client = AsyncAnthropic()
        self.model = model
        self.max_tokens = max_tokens
        self.budget_tokens = budget_tokens

    async def send(self, messages: list, tools: list,
                   system_prompt: str) -> ProviderResponse:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            thinking={
                "type": "enabled",
                "budget_tokens": self.budget_tokens,
            },
            system=system_prompt,
            tools=tools,
            messages=messages,
        )
        return self._map_response(response)

    def _map_response(self, response) -> ProviderResponse:
        thinking_parts = []
        content_blocks = []
        raw_content = []

        for block in response.content:
            raw_content.append(block)
            if block.type == "thinking":
                thinking_parts.append(block.thinking)
            else:
                content_blocks.append(block)

        # The API doesn't expose thinking_tokens separately — estimate
        # from thinking text length (~4 chars per token as rough heuristic)
        thinking_text = "\n".join(thinking_parts)
        thinking_tokens = len(thinking_text) // 4 if thinking_text else 0

        usage = TokenUsage(
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            thinking_tokens=thinking_tokens,
        )

        return ProviderResponse(
            thinking="\n".join(thinking_parts),
            content=content_blocks,
            raw_content=raw_content,
            usage=usage,
        )
