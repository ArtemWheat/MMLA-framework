"""Case registry and factories."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Awaitable, Callable, Dict, Optional, TYPE_CHECKING

from core.domain import CaseId

OrchestratorFactory = Callable[[], Awaitable["CaseOrchestrator"]]

if TYPE_CHECKING:
    from application.orchestrator import CaseOrchestrator


@dataclass
class CaseFactory:
    """Registry mapping case ids to orchestrator factories."""

    _registry: Dict[CaseId, OrchestratorFactory] = field(default_factory=dict)

    def register(self, case_id: CaseId, factory: OrchestratorFactory) -> None:
        self._registry[case_id] = factory

    def unregister(self, case_id: CaseId) -> None:
        self._registry.pop(case_id, None)

    def get(self, case_id: CaseId) -> Optional[OrchestratorFactory]:
        return self._registry.get(case_id)
