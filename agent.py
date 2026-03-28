"""Agent loop — owns conversation history and tool dispatch."""

import asyncio
from events import Event, EventBus
from providers.anthropic import AnthropicProvider, ProviderResponse


class Agent:
    def __init__(self, provider: AnthropicProvider, event_bus: EventBus,
                 tool_definitions: list[dict], tool_functions: dict,
                 approval_required: set[str], system_prompt: str,
                 tool_timeout: int = 120, max_tool_output: int = 10000):
        self.provider = provider
        self.event_bus = event_bus
        self.tool_definitions = tool_definitions
        self.tool_functions = tool_functions
        self.approval_required = approval_required
        self.system_prompt = system_prompt
        self.tool_timeout = tool_timeout
        self.max_tool_output = max_tool_output
        self.conversation_history: list[dict] = []
        self._approval_fn = None
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._total_thinking_tokens = 0

    def set_approval_fn(self, fn):
        self._approval_fn = fn

    async def run(self, user_input: str) -> str:
        self.conversation_history.append({
            "role": "user",
            "content": user_input,
        })

        tool_call_count = 0
        turn_thinking_tokens = 0

        while True:
            try:
                response = await self.provider.send(
                    self.conversation_history,
                    self.tool_definitions,
                    self.system_prompt,
                )
            except Exception as e:
                error_msg = f"API error: {e}"
                await self.event_bus.emit(Event("Stop", {
                    "total_tokens": self._total_input_tokens + self._total_output_tokens,
                    "thinking_tokens": turn_thinking_tokens,
                    "tool_calls": tool_call_count,
                    "error": error_msg,
                }))
                return error_msg

            self._total_input_tokens += response.usage.input_tokens
            self._total_output_tokens += response.usage.output_tokens
            self._total_thinking_tokens += response.usage.thinking_tokens
            turn_thinking_tokens += response.usage.thinking_tokens

            # Emit thinking and text to UI via event bus
            await self.event_bus.emit(Event("Response", {
                "thinking": response.thinking,
                "content": response.content,
                "usage": response.usage,
            }))

            # Append assistant turn with raw_content (TC-002: preserve thinking blocks)
            self.conversation_history.append({
                "role": "assistant",
                "content": response.raw_content,
            })

            # Extract tool_use blocks
            tool_calls = [b for b in response.content if b.type == "tool_use"]
            if not tool_calls:
                total = self._total_input_tokens + self._total_output_tokens
                await self.event_bus.emit(Event("Stop", {
                    "total_tokens": total,
                    "thinking_tokens": turn_thinking_tokens,
                    "tool_calls": tool_call_count,
                }))
                # Return final text
                text_parts = [b.text for b in response.content if b.type == "text"]
                return "\n".join(text_parts)

            # Process each tool call
            tool_results = []
            for tool_block in tool_calls:
                tool_name = tool_block.name
                tool_input = tool_block.input
                tool_use_id = tool_block.id
                tool_call_count += 1

                await self.event_bus.emit(Event("PreToolUse", {
                    "tool": tool_name,
                    "args": tool_input,
                }))

                # Check approval
                if tool_name in self.approval_required and self._approval_fn:
                    approved = await self._approval_fn(tool_name, tool_input)
                    if not approved:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": "Tool execution denied by user.",
                        })
                        await self.event_bus.emit(Event("PostToolUse", {
                            "tool": tool_name,
                            "total_tokens": self._total_input_tokens + self._total_output_tokens,
                            "thinking_tokens": response.usage.thinking_tokens,
                        }))
                        continue

                # Execute tool
                fn = self.tool_functions.get(tool_name)
                if fn is None:
                    result = f"Error: Unknown tool '{tool_name}'"
                else:
                    try:
                        result = await asyncio.wait_for(
                            fn(**tool_input), timeout=self.tool_timeout
                        )
                    except asyncio.TimeoutError:
                        result = f"Error: Tool '{tool_name}' timed out after {self.tool_timeout}s"
                    except Exception as e:
                        result = f"Error executing {tool_name}: {e}"

                # Truncate output
                if isinstance(result, str) and len(result) > self.max_tool_output:
                    result = result[:self.max_tool_output] + "\n... (truncated)"

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": result,
                })

                await self.event_bus.emit(Event("PostToolUse", {
                    "tool": tool_name,
                    "total_tokens": self._total_input_tokens + self._total_output_tokens,
                    "thinking_tokens": response.usage.thinking_tokens,
                }))

            # Append tool results to conversation history
            self.conversation_history.append({
                "role": "user",
                "content": tool_results,
            })
