"""Event bus abstractions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator, Generic, TypeVar

from core.domain.events import DomainEvent

TEvent = TypeVar("TEvent", bound=DomainEvent)


class IEventBus(ABC, Generic[TEvent]):
    """Pub-sub event bus contract."""

    @abstractmethod
    async def publish(self, event: TEvent) -> None:
        ...

    @abstractmethod
    async def subscribe(self, event_type: type[TEvent]) -> AsyncIterator[TEvent]:
        ...
