"""Predictor interfaces for validation and analytics stages."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from core.domain.data_models import PredictionInput, PredictionOutcome, PredictionStage


class BasePredictor(ABC):
    """Common predictor contract."""

    stage: PredictionStage

    @abstractmethod
    async def predict(self, request: PredictionInput) -> PredictionOutcome:
        """Run prediction for the given input."""


class BaseValidationPredictor(BasePredictor, ABC):
    stage = PredictionStage.VALIDATION


class BaseAnalyticsPredictor(BasePredictor, ABC):
    stage = PredictionStage.ANALYTICS
