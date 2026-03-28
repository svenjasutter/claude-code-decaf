"""Append a learned fact to .memory/MEMORY.md."""

import asyncio
from datetime import date
from pathlib import Path

SCHEMA = {
    "name": "update_memory",
    "description": "Persist a fact learned during this session so it is available in future sessions.",
    "input_schema": {
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "The fact to store.",
            },
            "reason": {
                "type": "string",
                "description": "Why the agent decided this is worth remembering.",
            },
        },
        "required": ["content", "reason"],
    },
}


async def update_memory(content: str, reason: str) -> str:
    def _write():
        memory_dir = Path(".memory")
        memory_dir.mkdir(exist_ok=True)
        memory_file = memory_dir / "MEMORY.md"

        today = date.today().isoformat()
        entry = f"- {today}: {content} ({reason})\n"

        with open(memory_file, "a") as f:
            f.write(entry)

        return f"Saved to MEMORY.md: {content}"

    return await asyncio.to_thread(_write)
