"""JSON structured logging listener — writes events to .logs/ as JSONL."""

import json
from datetime import datetime, timezone
from pathlib import Path
from events import Event, EventBus


class LoggingListener:
    def __init__(self):
        self._log_file = None

    def _ensure_log_file(self):
        if self._log_file is not None:
            return
        log_dir = Path(".logs")
        log_dir.mkdir(exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
        self._log_path = log_dir / f"{timestamp}.jsonl"
        self._log_file = open(self._log_path, "a")

    def _write(self, event: Event):
        self._ensure_log_file()
        entry = {
            "ts": event.timestamp,
            "event": event.event_type,
            "data": event.data,
        }
        self._log_file.write(json.dumps(entry, default=str) + "\n")
        self._log_file.flush()


def register_logging_listener(event_bus: EventBus) -> LoggingListener:
    listener = LoggingListener()

    async def _on_event(event: Event):
        listener._write(event)

    event_bus.subscribe("SessionStart", _on_event)
    event_bus.subscribe("PreToolUse", _on_event)
    event_bus.subscribe("PostToolUse", _on_event)
    event_bus.subscribe("Stop", _on_event)

    return listener
