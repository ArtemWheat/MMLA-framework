"""Stream handler interfaces and related contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Mapping, Optional, Protocol, Sequence

from core.domain.data_models import FrameBatch, FramePayload
from core.domain.value_objects import ChannelKey


@dataclass(frozen=True)
class ChannelSpec:
    """Descriptor of a single logical channel provided by a stream."""

    key: ChannelKey
    fmt: str
    required: bool = True
    description: Optional[str] = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StreamDescriptor:
    """Static description of a stream handler."""

    name: str
    channels: Sequence[ChannelSpec]
    multiplexed: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def required_channels(self) -> Sequence[ChannelSpec]:
        return [spec for spec in self.channels if spec.required]


class BaseStreamHandler(ABC):
    """Base class for concrete stream handlers."""

    descriptor: StreamDescriptor

    async def __aenter__(self) -> "BaseStreamHandler":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.stop()

    @abstractmethod
    async def start(self) -> None:
        """Allocate resources and prepare for streaming."""

    @abstractmethod
    async def stop(self) -> None:
        """Release resources."""

    @abstractmethod
    async def __aiter__(self) -> AsyncIterator[FrameBatch]:
        """Yield frame batches indefinitely until stopped."""


class IStreamHandler(Protocol):
    """Protocol version of stream handler for duck typing."""

    descriptor: StreamDescriptor

    async def start(self) -> None: ...

    async def stop(self) -> None: ...

    def __aiter__(self) -> AsyncIterator[FrameBatch]: ...


class IFrameMuxer(Protocol):
    """Component that aligns frames produced by multiple handlers."""

    async def mux(self, batches: Sequence[FrameBatch]) -> FrameBatch: ...


class IMultiChannelFrame(Protocol):
    """Representation of a multi-channel frame produced by a handler."""

    def channels(self) -> Sequence[ChannelKey]: ...

    def get(self, channel: ChannelKey) -> FramePayload: ...


class IDeviceProbe(Protocol):
    """Abstraction for probing device state before activation."""

    async def check_ready(self) -> bool: ...

    async def diagnostics(self) -> Mapping[str, Any]: ...
