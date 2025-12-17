"""Threshold-based analytics predictor."""

from __future__ import annotations

import numpy as np
from pydantic import BaseModel, Field

from core.domain import BasePredictionData, PredictionInput, PredictionOutcome
from core.interfaces.predictors import BaseAnalyticsPredictor


class ThresholdConfig(BaseModel):
    """Configuration for threshold_alert predictor."""

    threshold: int = Field(default=180, ge=0, le=255)


class ThresholdPredictor(BaseAnalyticsPredictor):
    """Raise alert when mean intensity exceeds threshold."""

    def __init__(self, config: ThresholdConfig) -> None:
        self.config = config

    async def predict(self, request: PredictionInput) -> PredictionOutcome:
        data = request.data
        assert isinstance(data, BasePredictionData)
        frame = np.array(next(iter(data.payloads.values())))
        mean_val = float(frame.mean())
        status = "alert" if mean_val > self.config.threshold else "ok"
        return PredictionOutcome.success_result(
            stage=self.stage,
            result={"mean": mean_val, "status": status},
        )
