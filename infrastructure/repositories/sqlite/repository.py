"""SQLite repository and unit-of-work implementations."""

from __future__ import annotations

import asyncio
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from core.domain import PredictionOutcome, SessionId
from core.domain.value_objects import PredictionId
from core.interfaces import IRepositoryDB, IUnitOfWork


def _ensure_schema(connection: sqlite3.Connection) -> None:
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS prediction_outcomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            stage TEXT NOT NULL,
            success INTEGER NOT NULL,
            result TEXT,
            artifacts TEXT,
            errors TEXT,
            metrics TEXT,
            duration_ms REAL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.commit()


class SqliteRepository(IRepositoryDB):
    """SQLite-backed repository implementation."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._connection.row_factory = sqlite3.Row

    async def save_prediction_outcome(self, session_id: SessionId, outcome: PredictionOutcome) -> PredictionId:
        def _insert() -> PredictionId:
            cursor = self._connection.cursor()
            cursor.execute(
                """
                INSERT INTO prediction_outcomes (
                    session_id, stage, success, result, artifacts, errors, metrics, duration_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    outcome.stage.value,
                    1 if outcome.success else 0,
                    json.dumps(outcome.result, default=str) if outcome.result is not None else None,
                    json.dumps([artifact.uri for artifact in outcome.artifacts]) if outcome.artifacts else None,
                    json.dumps(outcome.errors) if outcome.errors else None,
                    json.dumps(outcome.metrics) if outcome.metrics else None,
                    outcome.duration_ms,
                ),
            )
            self._connection.commit()
            return PredictionId(str(cursor.lastrowid))

        return await asyncio.to_thread(_insert)


@dataclass
class SqliteUnitOfWork(IUnitOfWork):
    """Unit-of-work for SQLite repository."""

    db_path: Path
    _connection: Optional[sqlite3.Connection] = None
    repository: SqliteRepository = None  # type: ignore[assignment]

    async def __aenter__(self) -> "SqliteUnitOfWork":
        def _connect() -> sqlite3.Connection:
            return sqlite3.connect(str(self.db_path), check_same_thread=False)

        self._connection = await asyncio.to_thread(_connect)
        await asyncio.to_thread(_ensure_schema, self._connection)
        self.repository = SqliteRepository(self._connection)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if not self._connection:
            return
        if exc:
            await self.rollback()
        else:
            await self.commit()
        await asyncio.to_thread(self._connection.close)
        self._connection = None

    async def commit(self) -> None:
        if self._connection:
            await asyncio.to_thread(self._connection.commit)

    async def rollback(self) -> None:
        if self._connection:
            await asyncio.to_thread(self._connection.rollback)
