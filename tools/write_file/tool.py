"""Write or overwrite a file on the filesystem."""

import asyncio
from pathlib import Path

SCHEMA = {
    "name": "write_file",
    "description": "Write content to a file at the given path. Creates parent directories if needed.",
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The file path to write to.",
            },
            "content": {
                "type": "string",
                "description": "The content to write to the file.",
            },
        },
        "required": ["path", "content"],
    },
}


async def write_file(path: str, content: str) -> str:
    def _write():
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return f"Successfully wrote {len(content)} characters to {path}"

    return await asyncio.to_thread(_write)
