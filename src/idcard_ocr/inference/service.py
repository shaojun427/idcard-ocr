"""High-level interface that ties together OCR detection and field parsing."""
from __future__ import annotations

from typing import Iterable, Sequence

from idcard_ocr.inference.engine import run_ocr
from idcard_ocr.inference.models import IdCardResult
from idcard_ocr.inference.parser import extract_text_lines, parse_id_card


def analyze_id_card(front_image: bytes, back_image: bytes) -> tuple[IdCardResult, list[str], list[str]]:
    """Run PaddleOCR on both sides of the ID card and parse structured data."""

    front_raw: Iterable[Sequence] = run_ocr(front_image)
    back_raw: Iterable[Sequence] = run_ocr(back_image)
    result = parse_id_card(front_raw, back_raw)
    front_text = extract_text_lines(front_raw)
    back_text = extract_text_lines(back_raw)
    return result, front_text, back_text
