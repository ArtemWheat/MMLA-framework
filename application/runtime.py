"""Runtime wiring for the MMLA framework."""

from __future__ import annotations

import asyncio
import logging
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, MutableSequence, Optional, Sequence

from configs.settings import settings
from core.domain import CaseConfigurationError, CaseId, DomainEvent, PredictionCompleted
from core.interfaces import IEventBus
from infrastructure.events.memory_bus import InMemoryEventBus
from infrastructure.repositories.sqlite.facade import SqliteRepositoryFacade
from infrastructure.storage.local_fs.file_storage import LocalArtifactStorage, LocalFileStorage
from application.artifacts import ArtifactPersistence
from application.cases.bootstrap import CaseBootstrapper
from application.cases.factories import CaseBuildContext, register_default_case_blueprints
from application.cases.registry import CaseFactory
from application.manager import CaseManager


async def _prediction_completed_consumer(
    event_bus: IEventBus[DomainEvent],
    artifact_persistence: ArtifactPersistence,
    repository: SqliteRepositoryFacade,
) -> None:
    async for event in event_bus.subscribe(PredictionCompleted):
        logger.info("PredictionCompleted received: case=%s stage=%s", event.case_id, event.outcome.stage)
        outcome = await artifact_persistence.handle_outcome(event.outcome, case_id=str(event.case_id))
        logger.info("Outcome artifacts after persistence: %s", [a.uri for a in outcome.artifacts])
        await repository.save_prediction_outcome(event.session_id, outcome)


logger = logging.getLogger(__name__)


@dataclass
class RuntimeEnvironment:
    """Aggregates application services and background consumers."""

    event_bus: IEventBus[DomainEvent]
    case_factory: CaseFactory
    case_manager: CaseManager
    bootstrapper: CaseBootstrapper
    artifact_persistence: ArtifactPersistence
    repository: SqliteRepositoryFacade
    registered_cases: Sequence[CaseId]
    background_tasks: MutableSequence[asyncio.Task] = field(default_factory=list)

    async def start(self) -> None:
        """Start background consumers if not already running."""
        if self.background_tasks:
            return
        task = asyncio.create_task(
            _prediction_completed_consumer(self.event_bus, self.artifact_persistence, self.repository),
            name="prediction_completed_consumer",
        )
        self.background_tasks.append(task)

    async def stop(self) -> None:
        """Cancel background consumers."""
        await self.case_manager.deactivate_all()
        for task in list(self.background_tasks):
            task.cancel()
        for task in list(self.background_tasks):
            with suppress(asyncio.CancelledError):
                await task
        self.background_tasks.clear()

    async def shutdown(self) -> None:
        """Convenience helper to deactivate cases and stop background tasks."""
        await self.stop()

    async def __aenter__(self) -> "RuntimeEnvironment":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.shutdown()


async def create_runtime(
    *,
    database_path: Optional[Path] = None,
    device_serials: Mapping[str, str] | None = None,
    metadata: Mapping[str, Mapping[str, object]] | None = None,
    overrides: Mapping[str, Mapping[str, object]] | None = None,
) -> RuntimeEnvironment:
    """
    Build application runtime with real event bus, storages and repository wiring.

    Parameters allow overriding database location, device serials, channel metadata
    and manifest overrides.
    """
    cases_dir = settings.cases_dir
    if not cases_dir.exists():
        raise CaseConfigurationError(
            f"Cases directory {cases_dir} not found. Set MMLA_CASES_ROOT."
        )

    models_dir = settings.models_dir
    if not models_dir.exists():
        raise CaseConfigurationError(
            f"Models directory {models_dir} not found. Set MMLA_MODELS_ROOT or ensure model artifacts are present."
        )

    db_path = (database_path or settings.database_file).resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    event_bus: IEventBus[DomainEvent] = InMemoryEventBus()
    case_factory = CaseFactory()
    bootstrapper = CaseBootstrapper(case_factory=case_factory)

    file_storage = LocalFileStorage(settings.data_dir)
    artifact_storage = LocalArtifactStorage(settings.artifacts_dir)
    artifact_persistence = ArtifactPersistence(file_storage=file_storage, artifact_storage=artifact_storage)

    repository = SqliteRepositoryFacade(db_path=db_path)
    context = CaseBuildContext(
        event_bus=event_bus,
        repository=repository,
        device_serials=device_serials or {},
        metadata=metadata or {},
        file_storage=file_storage,
    )
    register_default_case_blueprints(bootstrapper, context)
    registered_cases = await bootstrapper.bootstrap(overrides=overrides)

    case_manager = CaseManager(case_factory=case_factory, event_bus=event_bus)

    runtime = RuntimeEnvironment(
        event_bus=event_bus,
        case_factory=case_factory,
        case_manager=case_manager,
        bootstrapper=bootstrapper,
        artifact_persistence=artifact_persistence,
        repository=repository,
        registered_cases=registered_cases,
    )

    await runtime.start()
    return runtime
