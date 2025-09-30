"""Wrapper around PaddleOCR providing a simplified API for inference."""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Iterable, List, TYPE_CHECKING

from idcard_ocr.utils.image import decode_image_to_ndarray


class PaddleOCRNotAvailable(RuntimeError):
    """Raised when the Paddle OCR engine cannot be initialized."""


if TYPE_CHECKING:  # pragma: no cover - type hinting only
    from paddleocr import PaddleOCR


def _import_paddleocr():
    try:
        from paddleocr import PaddleOCR as _PaddleOCR
    except Exception as exc:  # pragma: no cover - import error path
        raise PaddleOCRNotAvailable("PaddleOCR package is not available") from exc
    return _PaddleOCR


def _build_paddleocr():
    PaddleOCR = _import_paddleocr()
    params: dict[str, Any] = {
        "use_angle_cls": True,
        "lang": "ch",
        "use_gpu": os.getenv("PADDLE_OCR_USE_GPU", "false").lower() in {"1", "true", "yes"},
    }
    det_model_dir = os.getenv("PADDLE_OCR_DET_MODEL_DIR")
    rec_model_dir = os.getenv("PADDLE_OCR_REC_MODEL_DIR")
    cls_model_dir = os.getenv("PADDLE_OCR_CLS_MODEL_DIR")
    if det_model_dir:
        params["det_model_dir"] = det_model_dir
    if rec_model_dir:
        params["rec_model_dir"] = rec_model_dir
    if cls_model_dir:
        params["cls_model_dir"] = cls_model_dir

    try:
        return PaddleOCR(**params)
    except Exception as exc:  # pragma: no cover - initialization paths
        raise PaddleOCRNotAvailable("Failed to initialize PaddleOCR") from exc


@lru_cache(maxsize=1)
def get_engine():
    """Return a cached PaddleOCR instance so models are loaded once."""

    return _build_paddleocr()


def run_ocr(image_bytes: bytes) -> List[list[Any]]:
    """Execute OCR on image bytes and return raw PaddleOCR detections."""

    image_array = decode_image_to_ndarray(image_bytes)
    engine = get_engine()
    return list(engine.ocr(image_array, cls=True))
