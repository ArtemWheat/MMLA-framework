"""Case catalog utilities for manifest discovery."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Mapping, MutableMapping, Sequence, Type, TypeVar

from configs.settings import settings
from core.domain import CaseId
from application.cases.loading import ManifestLoader

ManifestT = TypeVar("ManifestT")


@dataclass(frozen=True)
class CaseManifestSummary:
    """Lightweight description of a manifest discovered on disk."""

    case_id: CaseId
    slug: str
    path: Path
    data: Mapping[str, Any]


class CaseCatalog:
    """Scans the cases directory and exposes available manifests."""

    def __init__(self, loader: ManifestLoader | None = None) -> None:
        self.loader = loader or ManifestLoader()
        self._manifest_name = self.loader.manifest_name

    def discover(self) -> Sequence[CaseManifestSummary]:
        """Return summaries for all manifests present in the cases directory."""
        summaries: List[CaseManifestSummary] = []
        root = settings.cases_dir
        if not root.exists():
            return summaries

        for case_dir in sorted(p for p in root.iterdir() if p.is_dir()):
            manifest_path = case_dir / self._manifest_name
            if not manifest_path.is_file():
                continue
            raw: MutableMapping[str, Any] = self.loader.read(manifest_path)
            case_id_value = raw.get("case_id") or case_dir.name
            summaries.append(
                CaseManifestSummary(
                    case_id=CaseId(str(case_id_value)),
                    slug=case_dir.name,
                    path=manifest_path,
                    data=raw,
                )
            )
        return summaries

    def load(self, slug: str, model: Type[ManifestT], *, overrides: Mapping[str, Any] | None = None) -> ManifestT:
        """Load a manifest for the given slug into the provided Pydantic model."""
        return self.loader.load_default(slug, model, overrides=overrides)
