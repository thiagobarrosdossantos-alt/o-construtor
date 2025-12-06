"""
Testes unitários para Event Bus
"""
import pytest
from core.event_bus import EventBus


@pytest.mark.asyncio
async def test_event_bus_subscribe():
    """Testa subscrição de eventos"""
    bus = EventBus()
    events_received = []

    async def handler(event):
        events_received.append(event)

    bus.subscribe("test_event", handler)
    await bus.publish("test_event", {"data": "test"})

    assert len(events_received) == 1
    assert events_received[0]["data"] == "test"


@pytest.mark.asyncio
async def test_event_bus_multiple_subscribers():
    """Testa múltiplos subscribers"""
    bus = EventBus()
    events_1 = []
    events_2 = []

    async def handler_1(event):
        events_1.append(event)

    async def handler_2(event):
        events_2.append(event)

    bus.subscribe("test", handler_1)
    bus.subscribe("test", handler_2)

    await bus.publish("test", {"value": 42})

    assert len(events_1) == 1
    assert len(events_2) == 1


@pytest.mark.asyncio
async def test_event_bus_unsubscribe():
    """Testa remoção de subscription"""
    bus = EventBus()
    events = []

    async def handler(event):
        events.append(event)

    bus.subscribe("test", handler)
    bus.unsubscribe("test", handler)

    await bus.publish("test", {})

    assert len(events) == 0
