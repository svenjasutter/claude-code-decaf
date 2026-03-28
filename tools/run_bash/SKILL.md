# run_bash

Execute a shell command and return stdout and stderr combined.

## When to use
Use for build commands, test runners, and git operations.
Prefer read_file and write_file for file operations — they are
safer and produce cleaner tool results.

## Procedure
1. Pass the full command as a single string
2. Commands run from the project root by default
3. stdout and stderr are combined and returned to you

## Gotchas
- Commands are not interactive. Never use commands that prompt for input.
- There is no shell state between calls. Each call is a fresh subprocess —
  `cd` in one call does not carry over to the next.
- Long-running commands block the agent loop. Prefer commands that terminate.
- Destructive commands trigger approval before executing. This is intentional —
  do not try to work around it.
