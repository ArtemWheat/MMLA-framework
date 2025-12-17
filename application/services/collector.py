"""Collector service that transforms frame batches into prediction inputs."""

from __future__ import annotations

import inspect
import logging
from dataclasses import dataclass
from typing import Awaitable, Callable, Sequence

from core.domain import CaseId, FrameBatch, PredictionInput

PrepareCallable = Callable[[CaseId, FrameBatch], Awaitable[Sequence[PredictionInput]] | Sequence[PredictionInput]]


logger = logging.getLogger(__name__)


@dataclass
class CollectorService:
    """Wraps a callable that builds prediction inputs from frame batches."""

    prepare_inputs: PrepareCallable

    async def handle_batch(self, case_id: CaseId, batch: FrameBatch) -> Sequence[PredictionInput]:
        logger.info("Collector handling batch for case=%s with %d frames", case_id, len(batch.frames))
        result = self.prepare_inputs(case_id, batch)
        if inspect.isawaitable(result):
            result = await result  # type: ignore[assignment]
        logger.info("Collector produced %d prediction inputs", len(result))
        return result
