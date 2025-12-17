"""Case orchestrator coordinating collectors and predictors."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from dataclasses import dataclass, field
from typing import Optional

from core.domain import (
    CaseId,
    FrameBatch,
    FrameBatchReceived,
    PredictionCompleted,
    PredictionFailed,
    DomainEvent,
    SessionFailed,
    SessionId,
)
from application.services.collector import CollectorService
from application.services.predictor import PredictorService
from core.interfaces import BaseStreamHandler, IEventBus

logger = logging.getLogger(__name__)


@dataclass
class CaseOrchestrator:
    """Encapsulates a single case pipeline."""

    case_id: CaseId
    collector: CollectorService
    predictor: PredictorService
    event_bus: IEventBus[DomainEvent]
    stream_handler: BaseStreamHandler
    running: bool = False
    _task: Optional[asyncio.Task] = field(default=None, init=False, repr=False)

    async def start(self) -> None:
        if self.running:
            return
        await self.stream_handler.start()
        self.running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Orchestrator %s started stream handler %s", self.case_id, type(self.stream_handler).__name__)

    async def stop(self) -> None:
        if not self.running:
            return
        self.running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        logger.info("Orchestrator %s stopping stream handler", self.case_id)
        await self.stream_handler.stop()

    async def _run_loop(self) -> None:
        try:
            async for batch in self.stream_handler:
                logger.info(
                    "Orchestrator %s received batch session=%s frames=%d",
                    self.case_id,
                    batch.session_id,
                    len(batch.frames),
                )
                await self.event_bus.publish(FrameBatchReceived(case_id=self.case_id, batch=batch))
                prediction_inputs = await self.collector.handle_batch(self.case_id, batch)
                logger.info(
                    "Orchestrator %s prepared %d prediction inputs for session=%s",
                    self.case_id,
                    len(prediction_inputs),
                    batch.session_id,
                )
                for prediction_input in prediction_inputs:
                    logger.info(
                        "Orchestrator %s running stage=%s for session=%s",
                        self.case_id,
                        prediction_input.stage,
                        prediction_input.data.session_id,
                    )
                    outcome = await self.predictor.run(prediction_input)
                    logger.info(
                        "Orchestrator %s stage=%s success=%s duration=%.2fms session=%s",
                        self.case_id,
                        outcome.stage,
                        outcome.success,
                        outcome.duration_ms or -1.0,
                        prediction_input.data.session_id,
                    )
                    if outcome.success:
                        await self.event_bus.publish(
                            PredictionCompleted(case_id=self.case_id, session_id=prediction_input.data.session_id, outcome=outcome)
                        )
                        logger.debug(
                            "Orchestrator %s published PredictionCompleted for stage=%s session=%s",
                            self.case_id,
                            outcome.stage,
                            prediction_input.data.session_id,
                        )
                    else:
                        await self.event_bus.publish(
                            PredictionFailed(
                                case_id=self.case_id,
                                session_id=prediction_input.data.session_id,
                                stage=prediction_input.stage,
                                errors=outcome.errors or ("unknown error",),
                            )
                        )
                        logger.warning(
                            "Orchestrator %s published PredictionFailed for stage=%s session=%s errors=%s",
                            self.case_id,
                            prediction_input.stage,
                            prediction_input.data.session_id,
                            outcome.errors,
                        )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Orchestrator %s encountered error: %s", self.case_id, exc)
            await self.event_bus.publish(
                SessionFailed(case_id=self.case_id, session_id=SessionId("unknown"), reason=str(exc))
            )
            raise
