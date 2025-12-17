"""Case definitions and runners."""

from . import dummy_offline, resnet50_classification, yolov8_detection, threshold_alert

__all__ = [
    "dummy_offline",
    "yolov8_detection",
    "resnet50_classification",
    "threshold_alert",
]
