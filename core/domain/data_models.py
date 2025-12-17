"""Domain data models and containers used across the pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Iterable, Mapping, MutableMapping, Optional, Sequence

from core.domain.value_objects import ArtifactRef, CaseId, ChannelKey, PredictionId, SessionId


@dataclass(frozen=True)
class FramePayload:
    """Single frame or message coming from a handler."""

    channel: ChannelKey
    content: Any
    timestamp: datetime
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FrameBatch:
    """Group of payloads that should be processed together."""

    session_id: SessionId
    frames: Sequence[FramePayload]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def by_channel(self) -> Dict[ChannelKey, FramePayload]:
        """Return a mapping channel -> payload for quick lookup."""
        return {frame.channel: frame for frame in self.frames}


class PredictionStage(str, Enum):
    """Pipeline stages executed by predictors."""

    VALIDATION = "validation"
    ANALYTICS = "analytics"


@dataclass
class BasePredictionData:
    """Base class for structured inputs passed between predictors."""

    session_id: SessionId
    case_id: CaseId
    payloads: Mapping[ChannelKey, Any]
    metadata: MutableMapping[str, Any] = field(default_factory=dict)

    def has_channel(self, channel: ChannelKey) -> bool:
        return channel in self.payloads

    def require_channel(self, channel: ChannelKey) -> Any:
        if channel not in self.payloads:
            raise KeyError(f"Channel {channel!r} is missing in prediction data.")
        return self.payloads[channel]


@dataclass(frozen=True)
class PredictionInput:
    """Wrapper passed into predictors."""

    data: BasePredictionData
    stage: PredictionStage
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass
class PredictionOutcome:
    """Normalized result produced by predictors."""

    prediction_id: Optional[PredictionId]
    stage: PredictionStage
    success: bool
    result: Any
    artifacts: Sequence[ArtifactRef] = ()
    errors: Optional[Sequence[str]] = None
    metrics: MutableMapping[str, Any] = field(default_factory=dict)
    duration_ms: Optional[float] = None

    @classmethod
    def success_result(
        cls,
        stage: PredictionStage,
        result: Any,
        *,
        prediction_id: Optional[PredictionId] = None,
        artifacts: Sequence[ArtifactRef] = (),
        metrics: Optional[Mapping[str, Any]] = None,
        duration_ms: Optional[float] = None,
    ) -> "PredictionOutcome":
        outcome = cls(
            prediction_id=prediction_id,
            stage=stage,
            success=True,
            result=result,
            artifacts=tuple(artifacts),
            errors=None,
            duration_ms=duration_ms,
        )
        if metrics:
            outcome.metrics.update(metrics)
        return outcome

    @classmethod
    def failure_result(
        cls,
        stage: PredictionStage,
        errors: Sequence[str],
        *,
        prediction_id: Optional[PredictionId] = None,
        result: Any = None,
        duration_ms: Optional[float] = None,
    ) -> "PredictionOutcome":
        return cls(
            prediction_id=prediction_id,
            stage=stage,
            success=False,
            result=result,
            artifacts=(),
            errors=tuple(errors),
            duration_ms=duration_ms,
        )
