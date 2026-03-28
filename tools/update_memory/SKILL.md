# update_memory

Persist a fact learned during this session so it is available in future sessions.

## When to use
- User corrects your approach or assumptions
- You discover a non-obvious project convention
- A command behaves differently than expected
- A pattern is worth remembering across sessions

## When NOT to use
- Facts already in CLAUDE.md — they are already known
- Task-specific details that will not generalise to future sessions
- Anything the developer should write to CLAUDE.md themselves

## Procedure
1. Write one fact per call — multiple facts belong in separate calls
2. Make the `reason` specific: what happened that made this worth remembering?
3. Check loaded MEMORY.md first — do not duplicate existing entries

## Gotchas
- Vague reasons ("learned something useful") make the log unreadable and
  make it impossible to decide later whether to keep the memory.
- This tool is sandboxed to .memory/ — it cannot write elsewhere.
- The agent loop logs your `reason` as a PreToolUse event. It is visible
  to the developer in real time. Write it as if they are reading it.
