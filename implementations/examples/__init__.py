"""Example predictors and handlers shipped with the demo case."""

from implementations.examples.dummy import (
    DummyAnalyticsConfig,
    DummyHandlerConfig,
    DummyValidationConfig,
    DummyAnalyticsPredictor,
    DummyValidationPredictor,
    DummyStreamHandler,
    build_descriptor,
)
from implementations.examples.vision import (
    YoloV8DetectorConfig,
    YoloV8DetectionPredictor,
    ResNet50Config,
    ResNet50ClassifierPredictor,
)

__all__ = [
    "DummyAnalyticsConfig",
    "DummyHandlerConfig",
    "DummyValidationConfig",
    "DummyAnalyticsPredictor",
    "DummyValidationPredictor",
    "DummyStreamHandler",
    "build_descriptor",
    "YoloV8DetectorConfig",
    "YoloV8DetectionPredictor",
    "ResNet50Config",
    "ResNet50ClassifierPredictor",
]
