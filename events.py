"""Event bus and event dataclasses for the agent loop."""

import asyncio
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Event:
    event_type: str
    data: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class EventBus:
    def __init__(self):
        self._subscribers: dict[str, list] = {}

    def subscribe(self, event_type: str, callback):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    async def emit(self, event: Event):
        callbacks = self._subscribers.get(event.event_type, [])
        for callback in callbacks:
            try:
                await callback(event)
            except Exception:
                traceback.print_exc()
