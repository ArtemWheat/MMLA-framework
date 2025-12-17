"""Демонстрационный офлайн-кейс."""

from .collector import prepare_prediction_inputs
from .manifest import CASE_ID, CASE_SLUG, DummyOfflineManifest
from .blueprint import make_blueprint

__all__ = [
    "CASE_ID",
    "CASE_SLUG",
    "DummyOfflineManifest",
    "prepare_prediction_inputs",
    "make_blueprint",
]
