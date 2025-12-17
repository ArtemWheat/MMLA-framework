"""In-memory asyncio-based event bus implementation."""

from __future__ import annotations

import asyncio
from collections import defaultdict, deque
from typing import AsyncIterator, DefaultDict, Deque, Type, TypeVar

from core.domain import DomainEvent
from core.interfaces import IEventBus

TEvent = TypeVar("TEvent", bound=DomainEvent)


class InMemoryEventBus(IEventBus[TEvent]):
    """Simple in-memory pub-sub using asyncio queues."""

    def __init__(self) -> None:
        self._queues: DefaultDict[Type[TEvent], Deque[asyncio.Queue[TEvent]]] = defaultdict(lambda: deque())
        self._lock = asyncio.Lock()

    async def publish(self, event: TEvent) -> None:
        async with self._lock:
            queues = list(self._queues[type(event)])
        for queue in queues:
            await queue.put(event)

    async def subscribe(self, event_type: Type[TEvent]) -> AsyncIterator[TEvent]:
        queue: asyncio.Queue[TEvent] = asyncio.Queue()
        async with self._lock:
            self._queues[event_type].append(queue)
        try:
            while True:
                yield await queue.get()
        finally:
            async with self._lock:
                self._queues[event_type].remove(queue)
