"""Facade providing IRepositoryDB access via SQLite unit-of-work."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from core.domain import PredictionOutcome
from core.domain.value_objects import PredictionId, SessionId
from core.interfaces import IRepositoryDB
from infrastructure.repositories.factory import create_sqlite_uow


@dataclass
class SqliteRepositoryFacade(IRepositoryDB):
    """Wraps SqliteUnitOfWork to expose IRepositoryDB for consumers."""

    db_path: Path

    async def save_prediction_outcome(self, session_id: SessionId, outcome: PredictionOutcome) -> PredictionId:
        async with create_sqlite_uow(self.db_path) as uow:
            return await uow.repository.save_prediction_outcome(session_id, outcome)
