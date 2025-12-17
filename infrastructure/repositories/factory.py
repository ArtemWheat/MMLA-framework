"""Repository aggregation utilities."""

from __future__ import annotations

from pathlib import Path

from core.interfaces import IRepositoryDB, IUnitOfWork
from infrastructure.repositories.sqlite.repository import SqliteRepository, SqliteUnitOfWork


def create_sqlite_uow(db_path: Path) -> SqliteUnitOfWork:
    return SqliteUnitOfWork(db_path=db_path)

