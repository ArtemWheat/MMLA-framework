"""Pydantic settings for the framework."""

from __future__ import annotations

from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Base application settings."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="MMLA_", extra="allow")

    app_env: str = "development"
    cases_root: Path = Path("samples")
    manifest_name: str = "case.yaml"
    models_root: Path = Path("models")
    artifacts_root: Path = Path("artifacts")
    data_root: Path = Path("data")
    database_path: Path = Path("data/db.sqlite")

    @staticmethod
    def _resolve(path: Path) -> Path:
        return path if path.is_absolute() else (Path.cwd() / path).resolve()

    @field_validator("cases_root", "models_root", "artifacts_root", "data_root", "database_path", mode="before")
    @classmethod
    def _coerce_path(cls, value: str | Path) -> Path:  # noqa: D401
        """Ensure configured paths are converted into Path objects."""
        return Path(value)

    @property
    def cases_dir(self) -> Path:
        return self._resolve(self.cases_root)

    @property
    def models_dir(self) -> Path:
        return self._resolve(self.models_root)

    @property
    def artifacts_dir(self) -> Path:
        return self._resolve(self.artifacts_root)

    @property
    def data_dir(self) -> Path:
        return self._resolve(self.data_root)

    @property
    def database_file(self) -> Path:
        return self._resolve(self.database_path)


settings = AppSettings()
