"""Case manager orchestrating activation and lifecycle."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Sequence, TYPE_CHECKING

from core.domain import CaseActivated, CaseId, CaseConfigurationError, DomainEvent
from core.interfaces import IEventBus
from application.cases.registry import CaseFactory

if TYPE_CHECKING:
    from application.orchestrator import CaseOrchestrator


@dataclass
class CaseManager:
    """High-level entrypoint for activating/deactivating cases."""

    case_factory: CaseFactory
    event_bus: IEventBus[DomainEvent]
    active_cases: Dict[CaseId, "CaseOrchestrator"] = field(default_factory=dict)

    async def activate(self, case_id: CaseId) -> None:
        if case_id in self.active_cases:
            return

        provider = self.case_factory.get(case_id)
        if provider is None:
            raise CaseConfigurationError(f"Case {case_id} is not registered.")

        orchestrator = await provider()
        await orchestrator.start()
        self.active_cases[case_id] = orchestrator
        await self.event_bus.publish(CaseActivated(case_id=case_id))

    async def deactivate(self, case_id: CaseId) -> None:
        orchestrator = self.active_cases.pop(case_id, None)
        if orchestrator is None:
            return
        await orchestrator.stop()

    async def deactivate_all(self) -> None:
        """Deactivate all currently active cases."""
        for case_id in list(self.active_cases.keys()):
            await self.deactivate(case_id)

    def active_case_ids(self) -> Sequence[CaseId]:
        """Return identifiers of currently active cases."""
        return tuple(self.active_cases.keys())
