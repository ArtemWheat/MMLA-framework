"""Predictor service orchestrating stage-specific predictors."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Mapping

from core.domain import PredictionInput, PredictionOutcome, PredictionStage, PredictionConsistencyError
from core.interfaces import BasePredictor

logger = logging.getLogger(__name__)


@dataclass
class PredictorService:
    """Delegates prediction inputs to stage-specific predictors."""

    predictors: Mapping[PredictionStage, BasePredictor] = field(default_factory=dict)

    def register(self, stage: PredictionStage, predictor: BasePredictor) -> None:
        logger.info("Registered predictor for stage %s: %s", stage, type(predictor).__name__)
        self.predictors[stage] = predictor

    async def run(self, prediction_input: PredictionInput) -> PredictionOutcome:
        predictor = self.predictors.get(prediction_input.stage)
        if predictor is None:
            raise PredictionConsistencyError(f"No predictor registered for stage {prediction_input.stage}")
        logger.debug(
            "Dispatching predictor stage=%s handler=%s session=%s",
            prediction_input.stage,
            type(predictor).__name__,
            prediction_input.data.session_id,
        )
        start = time.time()
        outcome = await predictor.predict(prediction_input)
        elapsed_ms = (time.time() - start) * 1000.0
        if outcome.duration_ms is None:
            outcome.duration_ms = elapsed_ms
        outcome.metrics["duration_ms"] = outcome.duration_ms
        if isinstance(outcome.result, dict):
            outcome.result.setdefault("stage_duration_ms", outcome.duration_ms)
        logger.debug(
            "Predictor stage=%s completed success=%s duration=%.2fms session=%s",
            prediction_input.stage,
            outcome.success,
            outcome.duration_ms,
            prediction_input.data.session_id,
        )
        return outcome
