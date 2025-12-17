"""Dummy example components used by the built-in offline demo case."""

from .config import DummyAnalyticsConfig, DummyHandlerConfig, DummyValidationConfig
from .handler import DummyStreamHandler, build_descriptor
from .predictor import DummyAnalyticsPredictor, DummyValidationPredictor

__all__ = [
    "DummyHandlerConfig",
    "DummyValidationConfig",
    "DummyAnalyticsConfig",
    "DummyStreamHandler",
    "DummyAnalyticsPredictor",
    "DummyValidationPredictor",
    "build_descriptor",
]
