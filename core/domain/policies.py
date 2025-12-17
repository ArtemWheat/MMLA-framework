"""Domain policies and enums for pipeline orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class RetryStrategy(str, Enum):
    NEVER = "never"
    LIMITED = "limited"
    ALWAYS = "always"


class FailureAction(str, Enum):
    ABORT_SESSION = "abort_session"
    RETRY_STAGE = "retry_stage"
    FALLBACK = "fallback"


class StoragePolicy(str, Enum):
    DISCARD = "discard"
    TEMPORARY = "temporary"
    PERSIST = "persist"


@dataclass
class StagePolicy:
    max_attempts: int = 1
    retry_strategy: RetryStrategy = RetryStrategy.NEVER
    failure_action: FailureAction = FailureAction.ABORT_SESSION
    fallback_predictor: Optional[str] = None
