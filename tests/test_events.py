"""T101 — Unit tests for EventBus (events.py)."""

import pytest
from events import Event, EventBus


async def test_event_has_timestamp_and_type():
    e = Event(event_type="Stop", data={"x": 1})
    assert e.event_type == "Stop"
    assert e.data == {"x": 1}
    assert isinstance(e.timestamp, str)


async def test_subscribe_and_emit():
    bus = EventBus()
    received = []

    async def cb(event):
        received.append(event)

    bus.subscribe("Ping", cb)
    evt = Event("Ping", {"v": 42})
    await bus.emit(evt)

    assert len(received) == 1
    assert received[0] is evt


async def test_emit_no_subscribers():
    bus = EventBus()
    await bus.emit(Event("NoBody"))  # should not raise


async def test_multiple_subscribers():
    bus = EventBus()
    a, b = [], []

    async def cb_a(event):
        a.append(event)

    async def cb_b(event):
        b.append(event)

    bus.subscribe("X", cb_a)
    bus.subscribe("X", cb_b)
    await bus.emit(Event("X"))

    assert len(a) == 1
    assert len(b) == 1


async def test_subscriber_exception_does_not_crash(capsys):
    bus = EventBus()
    ok = []

    async def bad(event):
        raise RuntimeError("boom")

    async def good(event):
        ok.append(event)

    bus.subscribe("E", bad)
    bus.subscribe("E", good)
    await bus.emit(Event("E"))

    # good callback still ran despite bad raising
    assert len(ok) == 1
    # traceback was printed
    assert "boom" in capsys.readouterr().err


async def test_different_event_types_isolated():
    bus = EventBus()
    received = []

    async def cb(event):
        received.append(event.event_type)

    bus.subscribe("A", cb)
    await bus.emit(Event("B"))

    assert received == []

    await bus.emit(Event("A"))
    assert received == ["A"]
