"""Human-in-the-loop approval listener using async input."""

import json
from aioconsole import ainput


async def request_approval(tool_name: str, tool_input: dict) -> bool:
    print(f"\n🔒 Tool '{tool_name}' requires approval.")
    print(f"   Arguments: {json.dumps(tool_input, indent=2)}")
    while True:
        answer = await ainput("   Allow? (y/n): ")
        answer = answer.strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("   Please enter y or n.")
