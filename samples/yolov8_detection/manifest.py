"""Manifest models for the yolov8_detection demo case."""

from __future__ import annotations

from pydantic import BaseModel, Field

from core.domain import CaseId
from implementations.examples.dummy.config import DummyHandlerConfig
from implementations.examples.vision.config import YoloV8DetectorConfig

CASE_ID = CaseId("yolov8_detection")
CASE_SLUG = "yolov8_detection"


class YoloV8PredictorsConfig(BaseModel):
    analytics: YoloV8DetectorConfig = Field(default_factory=YoloV8DetectorConfig)


class YoloV8Manifest(BaseModel):
    handler: DummyHandlerConfig = Field(default_factory=DummyHandlerConfig)
    predictors: YoloV8PredictorsConfig = Field(default_factory=YoloV8PredictorsConfig)

    @property
    def case_id(self) -> CaseId:
        return CASE_ID
