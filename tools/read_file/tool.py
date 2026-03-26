"""Read a file from the filesystem."""

import asyncio
from pathlib import Path

SCHEMA = {
    "name": "read_file",
    "description": "Read the contents of a file at the given path.",
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The file path to read.",
            }
        },
        "required": ["path"],
    },
}


async def read_file(path: str) -> str:
    def _read():
        p = Path(path)
        if not p.exists():
            return f"Error: File not found: {path}"
        return p.read_text()

    content = await asyncio.to_thread(_read)
    return content[:10000]
