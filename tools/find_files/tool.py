"""Search for files by glob pattern."""

import asyncio
import glob as glob_module

SCHEMA = {
    "name": "find_files",
    "description": "Search for files matching a glob pattern.",
    "input_schema": {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "Glob pattern to match (e.g. '**/*.py').",
            },
            "path": {
                "type": "string",
                "description": "Directory to search in. Defaults to current directory.",
            },
        },
        "required": ["pattern"],
    },
}


async def find_files(pattern: str, path: str = ".") -> str:
    def _find():
        full_pattern = f"{path}/{pattern}"
        matches = sorted(glob_module.glob(full_pattern, recursive=True))
        if not matches:
            return f"No files found matching: {full_pattern}"
        return "\n".join(matches)

    result = await asyncio.to_thread(_find)
    return result[:10000]
