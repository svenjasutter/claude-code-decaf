# write_file

Write or overwrite a file at a given path. Creates parent directories if needed.

## When to use
Use for creating new files or replacing file contents entirely.
For small edits to existing files, consider reading first to avoid losing content.

## Procedure
1. Pass the full path and the complete file content
2. Parent directories are created automatically
3. Existing files are overwritten without warning

## Gotchas
- This tool requires approval before executing. The developer will be prompted.
- Overwrites the entire file — there is no append mode. Always include the full desired content.
- Does not create backups. If you need to preserve the original, read it first.
