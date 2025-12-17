# Пример: добавляем кейс `threshold_alert`

Цель: принимаем один RGB-канал, считаем среднее значение пикселей и сигнализируем, если оно выше порога. Кейс использует существующий синтетический `DummyStreamHandler`, поэтому никаких внешних устройств не нужно.

## Шаг 1. Манифест
`samples/threshold_alert/case.yaml`
```yaml
case_id: threshold_alert
handler:
  channels: ["rgb:main"]
  frame_shape: [32, 32]
  fps: 2.0
  max_batches: 5
predictors:
  analytics:
    threshold: 180
```

## Шаг 2. Collector
`samples/threshold_alert/collector.py`
```python
from core.domain import BasePredictionData, CaseId, FrameBatch, PredictionInput, PredictionStage
from core.domain.value_objects import ChannelKey

def prepare_prediction_inputs(case_id: CaseId, batch: FrameBatch) -> list[PredictionInput]:
    payloads = {ChannelKey(frame.channel): frame.content for frame in batch.frames}
    data = BasePredictionData(
        session_id=batch.session_id,
        case_id=case_id,
        payloads=payloads,
        metadata=dict(batch.metadata),
    )
    return [PredictionInput(stage=PredictionStage.ANALYTICS, data=data, metadata=dict(batch.metadata))]
```

## Шаг 3. Predictor
`samples/threshold_alert/predictor.py`
```python
import numpy as np
from pydantic import BaseModel, Field

from core.domain import BasePredictionData, PredictionInput, PredictionOutcome
from core.interfaces.predictors import BaseAnalyticsPredictor

class ThresholdConfig(BaseModel):
    threshold: int = Field(default=180, ge=0, le=255)

class ThresholdPredictor(BaseAnalyticsPredictor):
    def __init__(self, config: ThresholdConfig) -> None:
        self.config = config

    async def predict(self, request: PredictionInput) -> PredictionOutcome:
        data = request.data
        assert isinstance(data, BasePredictionData)
        frame = np.array(next(iter(data.payloads.values())))
        mean_val = float(frame.mean())
        status = "alert" if mean_val > self.config.threshold else "ok"
        return PredictionOutcome.success_result(
            stage=self.stage,
            result={"mean": mean_val, "status": status},
        )
```

## Шаг 4. Blueprint и манифест-модель
`samples/threshold_alert/manifest.py`
```python
from pydantic import BaseModel, Field
from core.domain import CaseId
from implementations.examples.dummy.config import DummyHandlerConfig
from samples.threshold_alert.predictor import ThresholdConfig

CASE_ID = CaseId("threshold_alert")
CASE_SLUG = "threshold_alert"

class ThresholdPredictorsConfig(BaseModel):
    analytics: ThresholdConfig = Field(default_factory=ThresholdConfig)

class ThresholdManifest(BaseModel):
    handler: DummyHandlerConfig = Field(default_factory=DummyHandlerConfig)
    predictors: ThresholdPredictorsConfig = Field(default_factory=ThresholdPredictorsConfig)

    @property
    def case_id(self) -> CaseId:
        return CASE_ID
```

`samples/threshold_alert/blueprint.py`
```python
from application.cases.bootstrap import CaseBlueprint
from application.cases.registry import OrchestratorFactory
from application.orchestrator import CaseOrchestrator
from application.services import CollectorService, PredictorService
from core.domain import PredictionStage
from implementations.examples.dummy.handler import DummyStreamHandler, build_descriptor
from samples.threshold_alert.collector import prepare_prediction_inputs
from samples.threshold_alert.predictor import ThresholdPredictor
from samples.threshold_alert.manifest import CASE_SLUG, ThresholdManifest

def make_blueprint(context) -> CaseBlueprint:
    def build_factory(manifest: ThresholdManifest) -> OrchestratorFactory:
        descriptor = build_descriptor(name=CASE_SLUG, channels=manifest.handler.channels)

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

    return CaseBlueprint(slug=CASE_SLUG, manifest_model=ThresholdManifest, build_factory=build_factory)
```

## Шаг 5. Регистрация
Добавьте модуль в `application/cases/factories.py`:
```python
BLUEPRINT_MODULES = [
    ...,
    "samples.threshold_alert.blueprint",
]
```

## Шаг 6. Запуск
```bash
python cli.py list
python cli.py run threshold_alert --duration 5
```

Этот кейс не требует реальных устройств и полностью работает на синтетических данных. Если нужно заменить поток на своё устройство, достаточно реализовать собственный `StreamHandler` и указать его в `blueprint.py`.
