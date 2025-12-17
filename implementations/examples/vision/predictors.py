"""Demo predictors that mimic YOLOv8 detection and ResNet50 classification outputs."""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np

from core.domain import BasePredictionData, PredictionInput, PredictionOutcome
from core.interfaces.predictors import BaseAnalyticsPredictor
from implementations.examples.vision.config import ResNet50Config, YoloV8DetectorConfig


class YoloV8DetectionPredictor(BaseAnalyticsPredictor):
    """Heuristic detector producing pseudo bounding boxes and scores."""

    def __init__(self, config: YoloV8DetectorConfig) -> None:
        self.config = config

    async def predict(self, request: PredictionInput) -> PredictionOutcome:
        data = request.data
        assert isinstance(data, BasePredictionData)
        detections: Dict[str, list[dict[str, Any]]] = {}
        for channel, payload in data.payloads.items():
            frame = np.array(payload, dtype=np.float32)
            # Simple heuristic: threshold bright regions and pick a few random-ish boxes.
            mean_val = frame.mean()
            std_val = frame.std()
            score = float(min(1.0, max(0.0, (mean_val + std_val) / 255.0)))
            channel_detections: list[dict[str, Any]] = []
            for idx, label in enumerate(self.config.class_names[: self.config.max_detections]):
                conf = max(self.config.score_threshold, score * (1.0 - idx * 0.05))
                box = {
                    "x1": 5 * (idx + 1),
                    "y1": 5 * (idx + 1),
                    "x2": 5 * (idx + 3),
                    "y2": 5 * (idx + 3),
                    "confidence": round(conf, 3),
                    "label": label,
                }
                channel_detections.append(box)
            detections[str(channel)] = channel_detections
        result = {"detections": detections}
        return PredictionOutcome.success_result(stage=self.stage, result=result)


class ResNet50ClassifierPredictor(BaseAnalyticsPredictor):
    """Heuristic classifier producing top-K labels with scores."""

    def __init__(self, config: ResNet50Config) -> None:
        self.config = config

    async def predict(self, request: PredictionInput) -> PredictionOutcome:
        data = request.data
        assert isinstance(data, BasePredictionData)
        predictions: Dict[str, list[dict[str, Any]]] = {}
        for channel, payload in data.payloads.items():
            frame = np.array(payload, dtype=np.float32)
            mean_val = frame.mean()
            norm = max(1e-6, frame.std() + mean_val / 255.0)
            scores = np.linspace(1.0, 0.2, num=len(self.config.class_names))
            scores = scores * (mean_val / 255.0) / norm
            top_indices = scores.argsort()[::-1][: self.config.top_k]
            channel_preds: list[dict[str, Any]] = []
            for idx in top_indices:
                channel_preds.append(
                    {
                        "label": self.config.class_names[idx],
                        "score": round(float(scores[idx]), 3),
                    }
                )
            predictions[str(channel)] = channel_preds
        result = {"predictions": predictions}
        return PredictionOutcome.success_result(stage=self.stage, result=result)
