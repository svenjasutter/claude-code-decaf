# list_directory

List files and directories at a given path.

## When to use
Use for a quick overview of directory contents before diving into specific files.
Prefer this over run_bash with ls — it handles missing directories gracefully.

## Procedure
1. Pass the directory path (defaults to current directory if omitted)
2. Directories are shown with a trailing `/`

## Gotchas
- Only lists immediate children — not recursive. Use find_files for deep searches.
- Hidden files (dotfiles) are included in the listing.
- Returns an error string if the path does not exist or is not a directory.
