"""Blueprint for the threshold_alert demo case."""

from __future__ import annotations

from typing import TYPE_CHECKING

from core.domain import PredictionStage
from application.cases.bootstrap import CaseBlueprint
from application.cases.registry import OrchestratorFactory
from application.orchestrator import CaseOrchestrator
from application.services import CollectorService, PredictorService
from implementations.examples.dummy.handler import DummyStreamHandler, build_descriptor
from samples.threshold_alert.collector import prepare_prediction_inputs
from samples.threshold_alert.predictor import ThresholdPredictor
from samples.threshold_alert.manifest import CASE_SLUG, ThresholdManifest

if TYPE_CHECKING:
    from application.cases.factories import CaseBuildContext


def make_blueprint(context: "CaseBuildContext") -> CaseBlueprint:
    slug_str = CASE_SLUG

    def build_factory(manifest: ThresholdManifest) -> OrchestratorFactory:
        descriptor = build_descriptor(name=slug_str, channels=manifest.handler.channels)

        async def factory() -> CaseOrchestrator:
            collector = CollectorService(prepare_prediction_inputs)
            predictor_service = PredictorService()
            predictor_service.register(PredictionStage.ANALYTICS, ThresholdPredictor(manifest.predictors.analytics))
            stream_handler = DummyStreamHandler(descriptor=descriptor, config=manifest.handler, case_id=manifest.case_id)

            return CaseOrchestrator(
                case_id=manifest.case_id,
                collector=collector,
                predictor=predictor_service,
                event_bus=context.event_bus,
                stream_handler=stream_handler,
            )

        return factory

    return CaseBlueprint(slug=slug_str, manifest_model=ThresholdManifest, build_factory=build_factory)
