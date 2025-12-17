"""Config models for vision demo predictors."""

from __future__ import annotations

from typing import List, Tuple

from pydantic import BaseModel, Field, PositiveFloat, PositiveInt


class YoloV8DetectorConfig(BaseModel):
    """Simplified detector config."""

    class_names: Tuple[str, ...] = Field(default=("person", "car", "bottle"))
    score_threshold: float = Field(default=0.25, ge=0.0, le=1.0)
    max_detections: PositiveInt = Field(default=5)


class ResNet50Config(BaseModel):
    """Simplified classifier config."""

    class_names: Tuple[str, ...] = Field(default=("cat", "dog", "car", "plane"))
    top_k: PositiveInt = Field(default=3, ge=1)
