"""Domain value objects shared across the framework."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Mapping, NewType, Optional
from types import MappingProxyType

SessionId = NewType("SessionId", str)
CaseId = NewType("CaseId", str)
ChannelKey = NewType("ChannelKey", str)
PredictionId = NewType("PredictionId", str)


@dataclass(frozen=True)
class ArtifactRef:
    """Lightweight reference to a stored artifact (file, blob, etc.)."""

    uri: str
    kind: str = "generic"
    metadata: Mapping[str, str] = field(default_factory=lambda: MappingProxyType({}))


@dataclass(frozen=True)
class TimestampedValue:
    """Typed value tagged with the moment it was produced."""

    value: object
    timestamp: datetime
    metadata: Optional[Mapping[str, object]] = None
