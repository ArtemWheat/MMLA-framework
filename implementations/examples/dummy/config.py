"""Pydantic configuration models for the dummy example case."""

from __future__ import annotations

from typing import Tuple

from pydantic import BaseModel, Field, PositiveInt


class DummyHandlerConfig(BaseModel):
    """Configure synthetic stream generation."""

    channels: Tuple[str, ...] = Field(default=("rgb:primary", "rgb:aux"))
    frame_shape: Tuple[PositiveInt, PositiveInt] = Field(default=(32, 32))
    fps: float = Field(default=2.0, gt=0.1, description="Frames per second for synthetic output.")
    max_batches: PositiveInt = Field(default=5, description="Number of batches to emit before stopping.")


class DummyValidationConfig(BaseModel):
    """Validation thresholds for incoming frames."""

    min_intensity: int = Field(default=0, ge=0, le=255)
    max_intensity: int = Field(default=255, ge=0, le=255)


class DummyAnalyticsConfig(BaseModel):
    """Analytics parameters for synthetic frame processing."""

    emit_histogram: bool = True
    top_k: PositiveInt = 3
