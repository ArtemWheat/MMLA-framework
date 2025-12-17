"""Repository and storage interfaces used by the pipeline."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from core.domain.data_models import PredictionOutcome
from core.domain.value_objects import ArtifactRef, PredictionId, SessionId


class IRepositoryDB(ABC):
    """Primary database access for prediction outcomes."""

    @abstractmethod
    async def save_prediction_outcome(
        self,
        session_id: SessionId,
        outcome: PredictionOutcome,
    ) -> PredictionId:
        """Persist prediction outcome and return its id."""


class IUnitOfWork(Protocol):
    """Unit-of-work contract for database operations."""

    repository: IRepositoryDB

    async def __aenter__(self) -> "IUnitOfWork": ...

    async def __aexit__(self, exc_type, exc, tb) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...


class IFileStorage(ABC):
    """Access to raw session data and artifacts on storage."""

    @abstractmethod
    async def save_bytes(self, *, path: str, data: bytes, overwrite: bool = False) -> ArtifactRef:
        ...

    @abstractmethod
    async def copy_tree(self, source: str, destination: str) -> None:
        ...

    @abstractmethod
    async def remove_tree(self, path: str) -> None:
        ...


class IArtifactStorage(ABC):
    """Logical storage for processed artifacts."""

    @abstractmethod
    async def store(self, *, artifact: ArtifactRef, payload: bytes) -> None:
        ...

    @abstractmethod
    async def fetch(self, artifact: ArtifactRef) -> bytes:
        ...

    @abstractmethod
    async def delete(self, artifact: ArtifactRef) -> None:
        ...
