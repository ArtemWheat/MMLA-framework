"""Measurement table configuration helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, Mapping, Optional, Tuple

from pydantic import BaseModel, Field, field_validator

from core.domain import CaseId

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class MeasurementColumnModel(BaseModel):
    """Pydantic model describing a measurement table column."""

    name: str
    type: str
    nullable: bool = True

    @field_validator("name")
    @classmethod
    def _validate_name(cls, value: str) -> str:
        if not _IDENTIFIER_RE.match(value):
            raise ValueError(f"Invalid column name '{value}'. Only letters, numbers and underscores are allowed.")
        return value


class MeasurementTableModel(BaseModel):
    """Pydantic model describing a measurement table."""

    table_name: str = Field(..., alias="name")
    columns: Tuple[MeasurementColumnModel, ...]

    @field_validator("table_name")
    @classmethod
    def _validate_table_name(cls, value: str) -> str:
        if not _IDENTIFIER_RE.match(value):
            raise ValueError(f"Invalid table name '{value}'. Only letters, numbers and underscores are allowed.")
        return value


@dataclass(frozen=True)
class MeasurementColumn:
    name: str
    type: str
    nullable: bool = True


@dataclass(frozen=True)
class MeasurementTable:
    table_name: str
    columns: Tuple[MeasurementColumn, ...]


def build_measurement_table(model: MeasurementTableModel) -> MeasurementTable:
    """Convert pydantic model to runtime configuration."""
    columns = tuple(MeasurementColumn(name=col.name, type=col.type, nullable=col.nullable) for col in model.columns)
    return MeasurementTable(table_name=model.table_name, columns=columns)


@dataclass
class MeasurementRegistry:
    """Runtime registry that keeps measurement table definitions per case."""

    _tables: Dict[CaseId, MeasurementTable] = field(default_factory=dict)

    def register(self, case_id: CaseId, table: MeasurementTable) -> None:
        self._tables[case_id] = table

    def get(self, case_id: CaseId) -> Optional[MeasurementTable]:
        return self._tables.get(case_id)

    def registered_cases(self) -> Iterable[CaseId]:
        return tuple(self._tables.keys())
