"""Execute a shell command and return stdout and stderr combined."""

import asyncio

SCHEMA = {
    "name": "run_bash",
    "description": "Execute a shell command and return stdout and stderr combined.",
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The shell command to execute.",
            }
        },
        "required": ["command"],
    },
}


async def run_bash(command: str) -> str:
    proc = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    return stdout.decode()[:10000]
