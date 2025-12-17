"""Blueprint for the resnet50_classification demo case."""

from __future__ import annotations

from typing import TYPE_CHECKING

from core.domain import PredictionStage
from application.cases.bootstrap import CaseBlueprint
from application.cases.registry import OrchestratorFactory
from application.orchestrator import CaseOrchestrator
from application.services import CollectorService, PredictorService
from implementations.examples.dummy.handler import DummyStreamHandler, build_descriptor
from implementations.examples.vision.predictors import ResNet50ClassifierPredictor

from .collector import prepare_prediction_inputs
from .manifest import CASE_SLUG, ResNet50Manifest

if TYPE_CHECKING:
    from application.cases.factories import CaseBuildContext


def make_blueprint(context: "CaseBuildContext") -> CaseBlueprint:
    slug_str = CASE_SLUG

    def build_factory(manifest: ResNet50Manifest) -> OrchestratorFactory:
        descriptor = build_descriptor(name=slug_str, channels=manifest.handler.channels)

        async def factory() -> CaseOrchestrator:
            collector = CollectorService(prepare_prediction_inputs)
            predictor_service = PredictorService()
            predictor_service.register(PredictionStage.ANALYTICS, ResNet50ClassifierPredictor(manifest.predictors.analytics))
            stream_handler = DummyStreamHandler(descriptor=descriptor, config=manifest.handler, case_id=manifest.case_id)

            return CaseOrchestrator(
                case_id=manifest.case_id,
                collector=collector,
                predictor=predictor_service,
                event_bus=context.event_bus,
                stream_handler=stream_handler,
            )

        return factory

    return CaseBlueprint(slug=slug_str, manifest_model=ResNet50Manifest, build_factory=build_factory)
