"""List contents of a directory."""

import asyncio
from pathlib import Path

SCHEMA = {
    "name": "list_directory",
    "description": "List files and directories at the given path.",
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Directory path to list. Defaults to current directory.",
            }
        },
        "required": [],
    },
}


async def list_directory(path: str = ".") -> str:
    def _list():
        p = Path(path)
        if not p.exists():
            return f"Error: Directory not found: {path}"
        if not p.is_dir():
            return f"Error: Not a directory: {path}"
        entries = sorted(p.iterdir())
        lines = []
        for entry in entries:
            suffix = "/" if entry.is_dir() else ""
            lines.append(f"{entry.name}{suffix}")
        if not lines:
            return "(empty directory)"
        return "\n".join(lines)

    return await asyncio.to_thread(_list)
