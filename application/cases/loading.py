"""Utilities for loading and validating case manifests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, MutableMapping, Type, TypeVar

import yaml
from pydantic import BaseModel

from configs.settings import settings

ManifestT = TypeVar("ManifestT", bound=BaseModel)


class ManifestNotFoundError(FileNotFoundError):
    """Raised when a manifest file is missing."""

    def __init__(self, path: Path) -> None:
        super().__init__(f"Manifest file not found: {path}")
        self.path = path


@dataclass
class ManifestLoader:
    """Loads YAML manifests into Pydantic models using application settings."""

    manifest_name: str = settings.manifest_name

    def default_path(self, case_slug: str) -> Path:
        """Return the default manifest path for the given case slug."""
        return settings.cases_dir / case_slug / self.manifest_name

    def read(self, path: Path) -> MutableMapping[str, Any]:
        """Read manifest YAML into a mutable mapping."""
        if not path.exists():
            raise ManifestNotFoundError(path)

        with path.open("r", encoding="utf-8") as fh:
            payload: MutableMapping[str, Any] = yaml.safe_load(fh) or {}
        return payload

    def load(
        self,
        model: Type[ManifestT],
        *,
        path: Path,
        overrides: Mapping[str, Any] | None = None,
    ) -> ManifestT:
        """Load YAML into the given Pydantic model."""
        payload = self.read(path)

        if overrides:
            payload.update(overrides)

        return model.model_validate(payload)

    def load_default(
        self,
        case_slug: str,
        model: Type[ManifestT],
        *,
        overrides: Mapping[str, Any] | None = None,
    ) -> ManifestT:
        """Load manifest for the given case slug using the default path."""
        manifest_path = self.default_path(case_slug)
        return self.load(model, path=manifest_path, overrides=overrides)
