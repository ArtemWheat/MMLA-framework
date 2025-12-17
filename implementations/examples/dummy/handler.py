"""Synthetic stream handler used by the dummy offline example."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Iterable, Sequence

import numpy as np

from core.domain import FrameBatch, FramePayload
from core.domain.value_objects import CaseId, ChannelKey, SessionId
from core.interfaces.streams import BaseStreamHandler, ChannelSpec, StreamDescriptor
from implementations.examples.dummy.config import DummyHandlerConfig


class DummyStreamHandler(BaseStreamHandler):
    """Produces synthetic RGB frames for multiple channels."""

    def __init__(self, *, descriptor: StreamDescriptor, config: DummyHandlerConfig, case_id: CaseId | None = None) -> None:
        self.descriptor = descriptor
        self.config = config
        self.case_id = case_id
        self._running = False
        self._batch_index = 0

    async def start(self) -> None:  # noqa: D401
        """Start synthetic stream generation."""
        self._running = True
        self._batch_index = 0

    async def stop(self) -> None:  # noqa: D401
        """Stop synthetic stream generation."""
        self._running = False

    def _make_session_id(self) -> SessionId:
        suffix = f"{self._batch_index:04d}"
        if self.case_id is None:
            return SessionId(f"dummy-{suffix}")
        return SessionId(f"{self.case_id}-{suffix}")

    def _build_payloads(self) -> Sequence[FramePayload]:
        height, width = self.config.frame_shape
        timestamp = datetime.utcnow()
        payloads: list[FramePayload] = []
        for idx, channel in enumerate(self.config.channels):
            noise = np.random.rand(height, width) * 255.0
            gradient = np.linspace(0, 255, num=width, dtype=np.float32)
            frame = np.tile(gradient, (height, 1)) + noise * 0.1 + idx * 10
            frame = np.clip(frame, 0, 255).astype(np.uint8)
            payloads.append(
                FramePayload(
                    channel=ChannelKey(channel),
                    content=frame,
                    timestamp=timestamp,
                    metadata={"channel_index": idx},
                )
            )
        return payloads

    async def __aiter__(self):
        while self._running and self._batch_index < self.config.max_batches:
            session_id = self._make_session_id()
            payloads = self._build_payloads()
            batch = FrameBatch(
                session_id=session_id,
                frames=payloads,
                metadata={"batch_index": self._batch_index, "case": str(self.case_id or "dummy")},
            )
            self._batch_index += 1
            yield batch
            await asyncio.sleep(1.0 / self.config.fps)
        self._running = False


def build_descriptor(name: str, channels: Iterable[str]) -> StreamDescriptor:
    specs = [ChannelSpec(key=ChannelKey(ch), fmt="rgb", description="synthetic channel") for ch in channels]
    return StreamDescriptor(name=name, channels=specs)
