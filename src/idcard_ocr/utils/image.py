"""Image loading helpers used by the OCR inference pipeline."""
from __future__ import annotations

from io import BytesIO

import numpy as np
from PIL import Image


class ImageDecodingError(RuntimeError):
    """Raised when an uploaded image cannot be decoded."""


def decode_image_to_ndarray(data: bytes) -> np.ndarray:
    """Convert raw image bytes to an RGB numpy array for PaddleOCR."""

    try:
        with Image.open(BytesIO(data)) as image:
            return np.array(image.convert("RGB"))
    except (OSError, ValueError) as exc:  # pragma: no cover - Pillow-specific errors
        raise ImageDecodingError("Failed to decode image bytes") from exc
