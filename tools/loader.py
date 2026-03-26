"""Dynamic tool loader — scans tools/ for SKILL.md files and loads schemas and functions."""

import asyncio
import importlib.util
import yaml
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent


def load_tools() -> tuple[list[dict], dict, set[str], list[str]]:
    """
    Scan tools/ for subdirs containing SKILL.md.

    Returns:
        tool_definitions  — list of SCHEMA dicts for the Anthropic API
        tool_functions    — {name: async_fn} for agent dispatch
        approval_required — set of tool names requiring approval
        skill_md_contents — list of SKILL.md contents for system prompt
    """
    config = yaml.safe_load((TOOLS_DIR / "config.yaml").read_text())
    approval_required = set(config.get("approval_required", []))

    tool_definitions: list[dict] = []
    tool_functions: dict = {}
    skill_md_contents: list[str] = []

    for tool_dir in sorted(TOOLS_DIR.iterdir()):
        if not tool_dir.is_dir():
            continue
        skill_md_path = tool_dir / "SKILL.md"
        if not skill_md_path.exists():
            continue

        skill_md = skill_md_path.read_text()
        skill_md_contents.append(skill_md)
        tool_py = tool_dir / "tool.py"

        if tool_py.exists():
            # Python tool — import SCHEMA and async function from tool.py
            spec = importlib.util.spec_from_file_location(
                f"tools.{tool_dir.name}.tool", tool_py
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            schema = module.SCHEMA
            fn = getattr(module, schema["name"])
        else:
            # CLI tool — generate a generic subprocess wrapper
            tool_name = tool_dir.name
            schema = {
                "name": tool_name,
                "description": skill_md,
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The CLI command to execute.",
                        }
                    },
                    "required": ["command"],
                },
            }

            # TC-001: Bind loop variable explicitly to avoid closure bug
            async def fn(command: str, _name: str = tool_name) -> str:
                proc = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                )
                stdout, _ = await proc.communicate()
                return stdout.decode()[:10000]

        tool_definitions.append(schema)
        tool_functions[schema["name"]] = fn

    return tool_definitions, tool_functions, approval_required, skill_md_contents
