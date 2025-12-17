"""Manifest models for the resnet50_classification demo case."""

from __future__ import annotations

from pydantic import BaseModel, Field

from core.domain import CaseId
from implementations.examples.dummy.config import DummyHandlerConfig
from implementations.examples.vision.config import ResNet50Config

CASE_ID = CaseId("resnet50_classification")
CASE_SLUG = "resnet50_classification"


class ResNetPredictorsConfig(BaseModel):
    analytics: ResNet50Config = Field(default_factory=ResNet50Config)


class ResNet50Manifest(BaseModel):
    handler: DummyHandlerConfig = Field(default_factory=DummyHandlerConfig)
    predictors: ResNetPredictorsConfig = Field(default_factory=ResNetPredictorsConfig)

    @property
    def case_id(self) -> CaseId:
        return CASE_ID
