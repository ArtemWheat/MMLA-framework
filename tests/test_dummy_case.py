from __future__ import annotations

import asyncio

from application.runtime import create_runtime
from configs.settings import settings
from core.domain import CaseId, PredictionCompleted, PredictionStage


def test_dummy_case_produces_predictions(tmp_path, monkeypatch):
    asyncio.run(_run_dummy_case(tmp_path, monkeypatch))


async def _run_dummy_case(tmp_path, monkeypatch):
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir()
    monkeypatch.setenv("MMLA_MODELS_ROOT", str(models_dir))
    monkeypatch.setenv("MMLA_DATA_ROOT", str(data_dir))
    monkeypatch.setenv("MMLA_ARTIFACTS_ROOT", str(artifacts_dir))
    monkeypatch.setenv("MMLA_DATABASE_PATH", str(tmp_path / "db.sqlite"))

    # Обновляем уже созданный экземпляр настроек, чтобы тестовые пути применились.
    settings.models_root = models_dir
    settings.data_root = data_dir
    settings.artifacts_root = artifacts_dir
    settings.database_path = tmp_path / "db.sqlite"

    overrides = {"dummy_offline": {"handler": {"max_batches": 1, "fps": 10}}}
    runtime = await create_runtime(overrides=overrides)
    events: list[PredictionCompleted] = []

    async def consumer():
        async for event in runtime.event_bus.subscribe(PredictionCompleted):
            if event.case_id == CaseId("dummy_offline"):
                events.append(event)
                if len(events) >= 2:
                    break

    consumer_task = asyncio.create_task(consumer())
    try:
        await runtime.case_manager.activate(CaseId("dummy_offline"))
        await asyncio.wait_for(consumer_task, timeout=5)
    finally:
        await runtime.case_manager.deactivate_all()
        await runtime.shutdown()
        if not consumer_task.done():
            consumer_task.cancel()

    stages = {event.outcome.stage for event in events}
    assert PredictionStage.VALIDATION in stages
    assert PredictionStage.ANALYTICS in stages
