"""Minimal blueprint registration utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module
from typing import Mapping, Optional

from core.domain import CaseId, DomainEvent
from core.interfaces import IEventBus, IRepositoryDB, IFileStorage
from application.cases.bootstrap import CaseBlueprint, CaseBootstrapper


@dataclass
class CaseBuildContext:
    """Runtime dependencies made available to blueprints."""

    event_bus: IEventBus[DomainEvent]
    repository: IRepositoryDB
    device_serials: Mapping[str, str] = field(default_factory=dict)
    metadata: Mapping[str, Mapping[str, object]] = field(default_factory=dict)
    file_storage: IFileStorage | None = None

    def device_serial_for(self, slug: str) -> Optional[str]:
        return self.device_serials.get(slug)

    def metadata_for(self, slug: str) -> Optional[Mapping[str, object]]:
        payload = self.metadata.get(slug)
        if payload is None:
            return None
        return dict(payload)

BLUEPRINT_MODULES = [
    "samples.dummy_offline.blueprint",
    "samples.yolov8_detection.blueprint",
    "samples.resnet50_classification.blueprint",
    "samples.threshold_alert.blueprint",
]


def register_default_case_blueprints(bootstrapper: CaseBootstrapper, context: CaseBuildContext) -> None:
    """Load and register all built-in blueprint modules."""
    for module_path in BLUEPRINT_MODULES:
        module = import_module(module_path)
        factory = getattr(module, "make_blueprint", None)
        if factory is None:
            raise RuntimeError(f"Blueprint module {module_path} does not define make_blueprint().")
        blueprint: CaseBlueprint = factory(context)
        bootstrapper.register_blueprint(blueprint)
