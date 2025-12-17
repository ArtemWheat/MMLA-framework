"""Predictors used by the dummy offline case."""

from __future__ import annotations

from typing import Any, Dict

import numpy as np

from core.domain import BasePredictionData, PredictionInput, PredictionOutcome
from core.interfaces.predictors import BaseAnalyticsPredictor, BaseValidationPredictor
from implementations.examples.dummy.config import DummyAnalyticsConfig, DummyValidationConfig


class DummyValidationPredictor(BaseValidationPredictor):
    """Simple sanity check: ensure channel mean intensity is within bounds."""

    def __init__(self, config: DummyValidationConfig) -> None:
        self.config = config

    async def predict(self, request: PredictionInput) -> PredictionOutcome:
        data = request.data
        assert isinstance(data, BasePredictionData)
        stats: Dict[str, float] = {}
        for channel, payload in data.payloads.items():
            frame = np.array(payload)
            mean_intensity = float(frame.mean())
            stats[str(channel)] = mean_intensity
            if mean_intensity < self.config.min_intensity or mean_intensity > self.config.max_intensity:
                return PredictionOutcome.failure_result(
                    stage=self.stage,
                    errors=(f"Channel {channel} intensity {mean_intensity:.2f} out of bounds",),
                    result={"channel": str(channel), "mean_intensity": mean_intensity},
                )
        return PredictionOutcome.success_result(
            stage=self.stage,
            result={"channels": stats, "status": "ok"},
        )


class DummyAnalyticsPredictor(BaseAnalyticsPredictor):
    """Generate summary statistics for each channel."""

    def __init__(self, config: DummyAnalyticsConfig) -> None:
        self.config = config

    async def predict(self, request: PredictionInput) -> PredictionOutcome:
        data = request.data
        assert isinstance(data, BasePredictionData)
        result: Dict[str, Any] = {"channels": {}}
        for channel, payload in data.payloads.items():
            frame = np.array(payload)
            mean_val = float(frame.mean())
            max_val = float(frame.max())
            min_val = float(frame.min())
            channel_metrics = {
                "mean": mean_val,
                "min": min_val,
                "max": max_val,
            }
            if self.config.emit_histogram:
                hist, _ = np.histogram(frame, bins=16, range=(0, 255))
                top_indices = hist.argsort()[-self.config.top_k :][::-1]
                channel_metrics["histogram_bins"] = hist.tolist()
                channel_metrics["top_bins"] = top_indices.tolist()
            result["channels"][str(channel)] = channel_metrics
        return PredictionOutcome.success_result(stage=self.stage, result=result)
