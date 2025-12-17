"""Collector callbacks for the dummy_offline case."""

from __future__ import annotations

from typing import Dict, List

from core.domain import BasePredictionData, CaseId, FrameBatch, PredictionInput, PredictionStage
from core.domain.value_objects import ChannelKey


def prepare_prediction_inputs(case_id: CaseId, batch: FrameBatch) -> List[PredictionInput]:
    """Split incoming batch into validation and analytics requests."""
    payloads: Dict[ChannelKey, object] = {ChannelKey(frame.channel): frame.content for frame in batch.frames}
    data = BasePredictionData(
        session_id=batch.session_id,
        case_id=case_id,
        payloads=payloads,
        metadata=dict(batch.metadata),
    )
    return [
        PredictionInput(stage=PredictionStage.VALIDATION, data=data, metadata=dict(batch.metadata)),
        PredictionInput(stage=PredictionStage.ANALYTICS, data=data, metadata=dict(batch.metadata)),
    ]
