"""Manifest models for the built-in dummy_offline case."""

from __future__ import annotations

from pydantic import BaseModel, Field

from core.domain import CaseId
from implementations.examples.dummy.config import DummyAnalyticsConfig, DummyHandlerConfig, DummyValidationConfig

CASE_ID = CaseId("dummy_offline")
CASE_SLUG = "dummy_offline"


class DummyPredictorsConfig(BaseModel):
    validation: DummyValidationConfig = Field(default_factory=DummyValidationConfig)
    analytics: DummyAnalyticsConfig = Field(default_factory=DummyAnalyticsConfig)


class DummyOfflineManifest(BaseModel):
    handler: DummyHandlerConfig = Field(default_factory=DummyHandlerConfig)
    predictors: DummyPredictorsConfig = Field(default_factory=DummyPredictorsConfig)

    @property
    def case_id(self) -> CaseId:
        return CASE_ID
