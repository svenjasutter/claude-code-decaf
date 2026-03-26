# read_file

Read the contents of a file at a given path.

## When to use
Use when you need to examine existing code, configuration, or documentation.
Prefer this over run_bash with cat — it handles missing files gracefully
and produces cleaner tool results.

## Procedure
1. Pass the full path to the file
2. Output is truncated to 10,000 characters

## Gotchas
- Returns an error string if the file does not exist — check the result before assuming content.
- Binary files will produce garbled output. Only use for text files.
- Large files are silently truncated. If you need the full file, use run_bash with wc -l first to check size.
