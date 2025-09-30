"""Pytest configuration that stubs heavy PaddleOCR dependency for unit tests."""
from __future__ import annotations

import os
import sys
from types import SimpleNamespace


if os.getenv("IDCARD_OCR_REAL_NUMPY", "0") not in {"1", "true", "True"}:
    class _NumpyStub(SimpleNamespace):  # pragma: no cover - simplified numpy shim
        float64 = float

        def array(self, value, dtype=None):
            return value

        def asarray(self, value, dtype=None):
            return value

        def mean(self, axis=None):  # pragma: no cover - not used but included for safety
            raise NotImplementedError

    sys.modules.setdefault("numpy", _NumpyStub())


class _StubPaddleOCR:  # pragma: no cover - simple stub for injection
    def __init__(self, *args, **kwargs):
        pass

    def ocr(self, image, cls=True):  # noqa: D401 - simple stub
        """Return empty detections; overridden in tests when needed."""

        return []


if "paddleocr" not in sys.modules:
    sys.modules["paddleocr"] = SimpleNamespace(PaddleOCR=_StubPaddleOCR)
