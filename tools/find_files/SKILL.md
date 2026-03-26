# find_files

Search for files matching a glob pattern.

## When to use
Use to discover files by name or extension before reading them.
Prefer this over run_bash with find — it is safer and produces cleaner results.

## Procedure
1. Pass a glob pattern (e.g. `**/*.py` for all Python files)
2. Optionally pass a path to search in (defaults to current directory)
3. Results are sorted alphabetically

## Gotchas
- Use `**` for recursive matching. A bare `*.py` only matches the top level.
- Output is truncated to 10,000 characters. In large repos, narrow your pattern.
- Returns an informative message if no files match — do not treat empty results as an error.
