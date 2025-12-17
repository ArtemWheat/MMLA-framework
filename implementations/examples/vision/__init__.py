"""Lightweight vision demo predictors (YOLOv8-style detection, ResNet50-style classification)."""

from .config import ResNet50Config, YoloV8DetectorConfig
from .predictors import ResNet50ClassifierPredictor, YoloV8DetectionPredictor

__all__ = [
    "YoloV8DetectorConfig",
    "YoloV8DetectionPredictor",
    "ResNet50Config",
    "ResNet50ClassifierPredictor",
]
