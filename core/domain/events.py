"""Domain events published across the pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping, Optional, Sequence

from core.domain.data_models import FrameBatch, PredictionOutcome, PredictionStage
from core.domain.value_objects import CaseId, SessionId


@dataclass(frozen=True)
class DomainEvent:
    """Base event with timestamp metadata."""

    occurred_at: datetime = field(default_factory=datetime.utcnow, init=False)


@dataclass(frozen=True)
class CaseActivated(DomainEvent):
    case_id: CaseId
    manifest_hash: Optional[str] = None


@dataclass(frozen=True)
class FrameBatchReceived(DomainEvent):
    case_id: CaseId
    batch: FrameBatch


@dataclass(frozen=True)
class PredictionStarted(DomainEvent):
    case_id: CaseId
    session_id: SessionId
    stage: PredictionStage
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PredictionCompleted(DomainEvent):
    case_id: CaseId
    session_id: SessionId
    outcome: PredictionOutcome


@dataclass(frozen=True)
class PredictionFailed(DomainEvent):
    case_id: CaseId
    session_id: SessionId
    stage: PredictionStage
    errors: Sequence[str]


@dataclass(frozen=True)
class SessionFailed(DomainEvent):
    case_id: CaseId
    session_id: SessionId
    reason: str
    details: Optional[Mapping[str, Any]] = None
