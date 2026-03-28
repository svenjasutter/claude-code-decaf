# prettier

Format source files using Prettier.

## When to use
Use after writing or modifying JavaScript, TypeScript, JSON, CSS, HTML,
or Markdown files that should follow the project's formatting rules.

## Procedure
1. Pass the full prettier command including the file path
2. Example: `prettier --write src/index.ts`
3. stdout shows which files were changed

## Gotchas
- Prettier must be installed in the project (`npx prettier` or global install).
- This tool requires approval before executing.
- The `--write` flag modifies files in place. Without it, prettier only prints formatted output to stdout.
- If prettier is not installed, the command will fail with a "command not found" error.
