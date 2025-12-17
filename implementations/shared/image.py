"""Generic image helpers reused across implementations."""

from __future__ import annotations

from pathlib import Path
from typing import Union

import cv2
import numpy as np
from PIL import Image

ImageInput = Union[Image.Image, np.ndarray, str, Path]


def to_pil(image_input: ImageInput) -> Image.Image:
    """Convert various image inputs to RGB PIL image."""
    if isinstance(image_input, Image.Image):
        return image_input.convert("RGB")

    if isinstance(image_input, np.ndarray):
        if image_input.ndim == 2:
            return Image.fromarray(image_input).convert("RGB")
        if image_input.ndim == 3 and image_input.shape[2] == 3:
            return Image.fromarray(cv2.cvtColor(image_input, cv2.COLOR_BGR2RGB))
        raise TypeError(f"Unsupported numpy image shape: {image_input.shape}")

    if isinstance(image_input, (str, Path)):
        return Image.open(image_input).convert("RGB")

    raise TypeError(f"Unsupported image input type: {type(image_input)}")
