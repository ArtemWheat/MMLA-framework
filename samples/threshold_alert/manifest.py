"""Manifest models for threshold_alert demo case."""

from __future__ import annotations

from pydantic import BaseModel, Field

from core.domain import CaseId
from implementations.examples.dummy.config import DummyHandlerConfig
from samples.threshold_alert.predictor import ThresholdConfig

CASE_ID = CaseId("threshold_alert")
CASE_SLUG = "threshold_alert"


class ThresholdPredictorsConfig(BaseModel):
    analytics: ThresholdConfig = Field(default_factory=ThresholdConfig)


class ThresholdManifest(BaseModel):
    handler: DummyHandlerConfig = Field(default_factory=DummyHandlerConfig)
    predictors: ThresholdPredictorsConfig = Field(default_factory=ThresholdPredictorsConfig)

    @property
    def case_id(self) -> CaseId:
        return CASE_ID
