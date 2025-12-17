"""Helpers for manifest-driven case registration."""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Awaitable, Callable, Dict, Mapping, Optional, Sequence, Type

from pydantic import BaseModel

from core.domain import CaseConfigurationError, CaseId
from application.cases.catalog import CaseCatalog
from application.cases.registry import CaseFactory, OrchestratorFactory

CaseBuilderResult = OrchestratorFactory | Awaitable[OrchestratorFactory]
CaseBuilderFn = Callable[[BaseModel], CaseBuilderResult]
Overrides = Mapping[str, Mapping[str, object]]


@dataclass
class CaseBlueprint:
    """Blueprint describing how to bootstrap a single case."""

    slug: str
    manifest_model: Type[BaseModel]
    build_factory: CaseBuilderFn


@dataclass
class CaseBootstrapper:
    """Coordinates manifest loading and registration of case orchestrators."""

    case_factory: CaseFactory
    catalog: CaseCatalog = field(default_factory=CaseCatalog)
    _blueprints: Dict[str, CaseBlueprint] = field(default_factory=dict)

    def register_blueprint(self, blueprint: CaseBlueprint) -> None:
        """Register a blueprint for a case slug."""
        self._blueprints[blueprint.slug] = blueprint

    def registered_slugs(self) -> Sequence[str]:
        return tuple(self._blueprints)

    async def bootstrap(self, *, overrides: Optional[Overrides] = None) -> Sequence[CaseId]:
        """
        Load manifests for registered blueprints and register orchestrator factories.

        Returns the list of case identifiers that were successfully registered.
        """
        overrides_map: Overrides = overrides or {}
        discovered = {summary.slug: summary for summary in self.catalog.discover()}
        registered: list[CaseId] = []

        for slug, blueprint in self._blueprints.items():
            if slug not in discovered:
                raise CaseConfigurationError(
                    f"Manifest for case '{slug}' not found (expected {self.catalog.loader.manifest_name})."
                )

            manifest_override = overrides_map.get(slug)
            manifest = self.catalog.load(slug, blueprint.manifest_model, overrides=manifest_override)

            factory_result = blueprint.build_factory(manifest)
            if inspect.isawaitable(factory_result):
                factory = await factory_result  # type: ignore[assignment]
            else:
                factory = factory_result

            if not callable(factory):
                raise CaseConfigurationError(f"Builder for case '{slug}' did not return a callable orchestrator factory.")

            case_id_value = getattr(manifest, "case_id", None)
            if case_id_value is None:
                raise CaseConfigurationError(f"Manifest for case '{slug}' does not define case_id.")
            if not isinstance(case_id_value, str):
                case_id_value = str(case_id_value)
            case_id = CaseId(case_id_value)

            self.case_factory.register(case_id, factory)
            registered.append(case_id)

        return tuple(registered)
