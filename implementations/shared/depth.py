"""Shared preprocessing routines for depth maps."""

from __future__ import annotations

import logging
from typing import Tuple

import cv2
import numpy as np

LOGGER = logging.getLogger(__name__)


def preprocess_depth_map(
    image: np.ndarray,
    target_size: Tuple[int, int] = (224, 224),
    *,
    enhance_contrast: bool = True,
    preserve_colors: bool = True,
) -> np.ndarray:
    """Crop background and normalise depth map for downstream models."""
    try:
        cropped = image

        if preserve_colors and image.ndim == 3 and image.shape[2] == 3:
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            blue_lower = np.array([110, 50, 50])
            blue_upper = np.array([130, 255, 255])
            blue_mask = cv2.inRange(hsv, blue_lower, blue_upper)
            object_mask = cv2.bitwise_not(blue_mask)

            kernel_small = np.ones((3, 3), np.uint8)
            kernel_large = np.ones((7, 7), np.uint8)
            object_mask = cv2.morphologyEx(object_mask, cv2.MORPH_CLOSE, kernel_small)
            object_mask = cv2.morphologyEx(object_mask, cv2.MORPH_OPEN, kernel_small)
            object_mask = cv2.morphologyEx(object_mask, cv2.MORPH_CLOSE, kernel_large)

            contours, _ = cv2.findContours(object_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                largest = max(contours, key=cv2.contourArea)
                hull = cv2.convexHull(largest)
                x, y, w, h = cv2.boundingRect(hull)
                padding_w = max(5, int(w * 0.08))
                padding_h = max(5, int(h * 0.08))
                x = max(0, x - padding_w)
                y = max(0, y - padding_h)
                w = min(image.shape[1] - x, w + 2 * padding_w)
                h = min(image.shape[0] - y, h + 2 * padding_h)
                cropped = image[y : y + h, x : x + w]

        if cropped.ndim == 3:
            if preserve_colors:
                lab = cv2.cvtColor(cropped, cv2.COLOR_BGR2LAB)
                gray = lab[:, :, 0]
            else:
                gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
        else:
            gray = cropped

        if enhance_contrast:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            gray = clahe.apply(gray)

            h, w = gray.shape
            center_y, center_x = h // 2, w // 2
            center_size = min(h, w) // 3
            if center_size > 10:
                y1 = max(0, center_y - center_size // 2)
                y2 = min(h, center_y + center_size // 2)
                x1 = max(0, center_x - center_size // 2)
                x2 = min(w, center_x + center_size // 2)
                center_region = gray[y1:y2, x1:x2]
                if center_region.size > 0 and len(np.unique(center_region)) > 10:
                    enhanced_center = cv2.equalizeHist(center_region)
                    gray[y1:y2, x1:x2] = cv2.addWeighted(center_region, 0.8, enhanced_center, 0.2, 0)

        h, w = gray.shape
        aspect_ratio = w / h
        target_aspect = target_size[1] / target_size[0]

        if aspect_ratio > target_aspect:
            new_w = target_size[1]
            new_h = int(target_size[1] / aspect_ratio)
        else:
            new_h = target_size[0]
            new_w = int(target_size[0] * aspect_ratio)

        if new_w > w or new_h > h:
            resized = cv2.resize(gray, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
        else:
            resized = cv2.resize(gray, (new_w, new_h), interpolation=cv2.INTER_AREA)

        final = np.zeros(target_size, dtype=np.uint8)
        y_offset = (target_size[0] - new_h) // 2
        x_offset = (target_size[1] - new_w) // 2
        final[y_offset : y_offset + new_h, x_offset : x_offset + new_w] = resized
        return final
    except Exception as exc:  # noqa: BLE001
        LOGGER.exception("Failed to preprocess depth map: %s", exc)
        return np.zeros(target_size, dtype=np.uint8)


def validate_depth_map(depth_map: np.ndarray) -> bool:
    """Check whether the depth map matches expected format."""
    return depth_map is not None and depth_map.shape == (224, 224)
