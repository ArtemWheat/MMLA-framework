"""Domain layer constructs."""

from core.domain.data_models import BasePredictionData, FrameBatch, FramePayload, PredictionInput, PredictionOutcome, PredictionStage
from core.domain.errors import CaseConfigurationError, DomainError, PredictionConsistencyError
from core.domain.events import (
    CaseActivated,
    DomainEvent,
    FrameBatchReceived,
    PredictionCompleted,
    PredictionFailed,
    PredictionStarted,
    SessionFailed,
)
from core.domain.policies import FailureAction, RetryStrategy, StagePolicy, StoragePolicy
from core.domain.use_cases import AsyncUseCase, UseCase
from core.domain.value_objects import ArtifactRef, CaseId, ChannelKey, PredictionId, SessionId, TimestampedValue

__all__ = [
    "BasePredictionData",
    "FrameBatch",
    "FramePayload",
    "PredictionInput",
    "PredictionOutcome",
    "PredictionStage",
    "DomainError",
    "PredictionConsistencyError",
    "CaseConfigurationError",
    "DomainEvent",
    "CaseActivated",
    "FrameBatchReceived",
    "PredictionStarted",
    "PredictionCompleted",
    "PredictionFailed",
    "SessionFailed",
    "FailureAction",
    "RetryStrategy",
    "StoragePolicy",
    "StagePolicy",
    "UseCase",
    "AsyncUseCase",
    "ArtifactRef",
    "CaseId",
    "ChannelKey",
    "PredictionId",
    "SessionId",
    "TimestampedValue",
]
