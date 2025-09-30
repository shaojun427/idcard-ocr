"""Utilities to transform raw OCR detections into structured ID card fields."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List, Sequence

from idcard_ocr.inference.models import BackSideResult, FieldResult, FrontSideResult, IdCardResult

_LABEL_PATTERNS = {
    "name": ("姓名",),
    "gender": ("性别",),
    "ethnicity": ("民族",),
    "birth_date": ("出生", "出生日期"),
    "address": ("住址",),
    "id_number": ("公民身份号码", "身份证号", "身份号码"),
    "issuing_authority": ("签发机关",),
    "valid_period": ("有效期限", "有效期", "有效日期"),
}

_LABEL_TOLERANCE = {
    "ethnicity": 1,
    "birth_date": 1,
}

_ID_NUMBER_PATTERN = re.compile(r"[0-9Xx]{15,18}")
_DATE_PATTERN = re.compile(
    r"(19|20)\d{2}(?:\s*[年.-]\s*)?(1[0-2]|0?[1-9])(?:\s*[月.-]\s*)?(3[01]|[12]\d|0?[1-9])\s*日?"
)
_PERIOD_PATTERN = re.compile(
    r"(19|20)\d{2}[.年-](1[0-2]|0?[1-9])[.月-](3[01]|[12]\d|0?[1-9])日?\s*[-~到至]\s*"
    r"(长期|(19|20)\d{2}[.年-](1[0-2]|0?[1-9])[.月-](3[01]|[12]\d|0?[1-9])日?)"
)
_GENDER_VALUE_PATTERN = re.compile(r"男|女")
_ETHNICITY_SUFFIX = "族"
_ETHNICITY_INLINE_PATTERN = re.compile(r"民族[：:\s]*([\w\u4e00-\u9fa5]+)")


@dataclass(slots=True)
class Line:
    text: str
    normalized: str
    confidence: float


def _normalize_text(text: str) -> str:
    return text.replace(" ", "").replace(":", "：").strip()


def _iter_detections(raw: Iterable[Sequence]) -> List[Line]:
    detections: List[Line] = []
    if not raw:
        return detections

    def _looks_like_detection(item: Sequence) -> bool:
        if not isinstance(item, (list, tuple)) or len(item) < 2:
            return False
        candidate = item[1]
        if isinstance(candidate, (list, tuple)) and candidate:
            return isinstance(candidate[0], str)
        return False

    if isinstance(raw, list):
        candidate: List[Sequence] = list(raw)
    else:
        candidate = list(raw)

    # Flatten nested structures produced by PaddleOCR until detections are found.
    while candidate and not any(_looks_like_detection(item) for item in candidate):
        next_level: List[Sequence] = []
        for item in candidate:
            if isinstance(item, (list, tuple)):
                next_level.extend(item)
        if not next_level or next_level == candidate:
            break
        candidate = next_level

    for det in candidate:
        if not _looks_like_detection(det):
            continue
        try:
            _, (text, score) = det
        except (TypeError, ValueError):
            continue
        if not text:
            continue
        detections.append(Line(text=text, normalized=_normalize_text(text), confidence=float(score)))
    return detections


def _starts_with_any(line: Line, labels: tuple[str, ...], tolerance: int = 0) -> bool:
    return _match_label_and_remainder(line.normalized, labels, tolerance)[1] is not None


def _match_label_and_remainder(
    text: str, labels: tuple[str, ...], tolerance: int
) -> tuple[str | None, int | None]:
    for label in labels:
        match_len = _label_match_length(text, label, tolerance)
        if match_len is None:
            continue
        remainder = text[match_len:].lstrip("：:")
        return remainder, match_len
    return None, None


def _label_match_length(text: str, label: str, tolerance: int) -> int | None:
    if len(text) < len(label):
        return None
    prefix = text[: len(label)]
    if prefix == label:
        return len(label)
    if tolerance <= 0:
        return None
    distance = sum(1 for left, right in zip(prefix, label) if left != right)
    if distance <= tolerance:
        return len(label)
    return None


def _should_stop_collecting(line: Line, key: str) -> bool:
    if _ID_NUMBER_PATTERN.search(line.normalized):
        return True
    for other_key, other_patterns in _LABEL_PATTERNS.items():
        if other_key == key:
            continue
        tolerance = _LABEL_TOLERANCE.get(other_key, 0)
        if _starts_with_any(line, other_patterns, tolerance):
            return True
    return False


def _collect_following_lines(
    lines: List[Line],
    start_idx: int,
    key: str,
    tolerance: int,
    *,
    initial_value: str = "",
) -> tuple[str, List[Line]]:
    fragments: List[str] = []
    collected: List[Line] = []
    digits = re.sub(r"[^0-9]", "", initial_value) if key == "birth_date" else None

    for follow in lines[start_idx:]:
        if _starts_with_any(follow, _LABEL_PATTERNS[key], tolerance):
            continue
        if _should_stop_collecting(follow, key):
            break
        collected.append(follow)
        fragments.append(follow.normalized)
        if digits is not None:
            digits = re.sub(r"[^0-9]", "", initial_value + "".join(fragments))
            if len(digits) >= 8:
                break

    return "".join(fragments), collected


def _extract_value(lines: List[Line], key: str) -> tuple[str | None, List[Line]]:
    patterns = _LABEL_PATTERNS[key]
    tolerance = _LABEL_TOLERANCE.get(key, 0)
    for idx, line in enumerate(lines):
        remainder, match_len = _match_label_and_remainder(line.normalized, patterns, tolerance)
        if match_len is None:
            continue
        consumed = [line]
        if remainder:
            if key == "birth_date":
                extra_value, extra_lines = _collect_following_lines(
                    lines, idx + 1, key, tolerance, initial_value=remainder
                )
                if extra_lines:
                    consumed.extend(extra_lines)
                    remainder += extra_value
            return remainder, consumed
        if key in {"address", "birth_date"}:
            extra_value, extra_lines = _collect_following_lines(lines, idx + 1, key, tolerance)
            if extra_lines:
                consumed.extend(extra_lines)
                return extra_value, consumed
        if idx + 1 < len(lines):
            next_line = lines[idx + 1]
            if _ID_NUMBER_PATTERN.search(next_line.normalized):
                continue
            if any(
                _starts_with_any(next_line, other_patterns, _LABEL_TOLERANCE.get(other_key, 0))
                for other_key, other_patterns in _LABEL_PATTERNS.items()
                if other_key != key
            ):
                continue
            consumed.append(next_line)
            return next_line.normalized, consumed
    return None, []


def _extract_id_number(lines: List[Line]) -> tuple[str | None, List[Line]]:
    for line in lines:
        match = _ID_NUMBER_PATTERN.search(line.normalized)
        if match:
            value = match.group(0).upper()
            return value, [line]
    return None, []


def _clean_ethnicity_value(value: str) -> str:
    cleaned = value.replace("民族", "").strip()
    for prefix in ("性别男", "性别女", "性别"):
        cleaned = cleaned.replace(prefix, "")
    if cleaned.startswith("男") or cleaned.startswith("女"):
        cleaned = cleaned[1:]
    if cleaned.endswith(_ETHNICITY_SUFFIX):
        cleaned = cleaned[:-1]
    return cleaned.strip()


def _extract_birth_date(lines: List[Line]) -> tuple[str | None, List[Line]]:
    for line in lines:
        match = _DATE_PATTERN.search(line.normalized)
        if match:
            normalized = _normalize_birth_date(match.group(0))
            if normalized:
                return normalized, [line]
    return None, []


def _extract_gender(lines: List[Line]) -> tuple[str | None, List[Line]]:
    for line in lines:
        if "性别" not in line.normalized:
            continue
        match = _GENDER_VALUE_PATTERN.search(line.normalized)
        if match:
            return match.group(0), [line]
    for line in lines:
        match = _GENDER_VALUE_PATTERN.search(line.normalized)
        if match:
            return match.group(0), [line]
    return None, []


def _extract_ethnicity(lines: List[Line]) -> tuple[str | None, List[Line]]:
    for line in lines:
        match = _ETHNICITY_INLINE_PATTERN.search(line.normalized)
        if not match:
            continue
        candidate = _clean_ethnicity_value(match.group(1))
        if candidate:
            return candidate, [line]
    for line in lines:
        if _ETHNICITY_SUFFIX in line.normalized:
            candidate = _clean_ethnicity_value(line.normalized)
            return candidate, [line]
    return None, []


def _extract_period(lines: List[Line]) -> tuple[str | None, List[Line]]:
    for line in lines:
        match = _PERIOD_PATTERN.search(line.normalized)
        if match:
            value = match.group(0)
            value = value.replace("年", ".").replace("月", ".").replace("日", "")
            value = value.replace("到", "-").replace("至", "-").replace("~", "-")
            value = re.sub(r"\.\.", ".", value)
            return value, [line]
    return None, []


def _aggregate_confidence(consumed: List[Line]) -> float | None:
    if not consumed:
        return None
    return sum(line.confidence for line in consumed) / len(consumed)


def parse_id_card(front_raw: Iterable[Sequence], back_raw: Iterable[Sequence]) -> IdCardResult:
    """Convert PaddleOCR outputs for both sides into structured results."""

    front_lines = _iter_detections(front_raw)
    back_lines = _iter_detections(back_raw)

    name_value, name_lines = _extract_value(front_lines, "name")
    gender_value, gender_lines = _extract_gender(front_lines)
    if not gender_value:
        gender_value, gender_lines = _extract_value(front_lines, "gender")
    ethnicity_value, ethnicity_lines = _extract_ethnicity(front_lines)
    if not ethnicity_value:
        ethnicity_value, ethnicity_lines = _extract_value(front_lines, "ethnicity")
    birth_value, birth_lines = _extract_birth_date(front_lines)
    if not birth_value:
        birth_value, birth_lines = _extract_value(front_lines, "birth_date")
    if birth_value:
        normalized_birth = _normalize_birth_date(birth_value)
        if normalized_birth:
            birth_value = normalized_birth
    address_value, address_lines = _extract_value(front_lines, "address")
    id_number_value, id_number_lines = _extract_id_number(front_lines)
    if not id_number_value:
        id_number_value, id_number_lines = _extract_value(front_lines, "id_number")

    issuing_value, issuing_lines = _extract_value(back_lines, "issuing_authority")
    period_value, period_lines = _extract_period(back_lines)
    if not period_value:
        period_value, period_lines = _extract_value(back_lines, "valid_period")

    front = FrontSideResult(
        name=FieldResult(value=name_value, confidence=_aggregate_confidence(name_lines)),
        gender=FieldResult(value=gender_value, confidence=_aggregate_confidence(gender_lines)),
        ethnicity=FieldResult(value=ethnicity_value, confidence=_aggregate_confidence(ethnicity_lines)),
        birth_date=FieldResult(value=birth_value, confidence=_aggregate_confidence(birth_lines)),
        address=FieldResult(value=address_value, confidence=_aggregate_confidence(address_lines)),
        id_number=FieldResult(value=id_number_value, confidence=_aggregate_confidence(id_number_lines)),
    )
    back = BackSideResult(
        issuing_authority=FieldResult(value=issuing_value, confidence=_aggregate_confidence(issuing_lines)),
        valid_period=FieldResult(value=period_value, confidence=_aggregate_confidence(period_lines)),
    )

    return IdCardResult(front=front, back=back)


def _normalize_birth_date(value: str) -> str | None:
    digits = re.sub(r"[^0-9]", "", value)
    if len(digits) >= 8:
        digits = digits[:8]
        year, month, day = digits[:4], digits[4:6], digits[6:8]
        return f"{year}-{month}-{day}"

    sanitized = value.replace("年", "-").replace("月", "-").replace("日", "")
    sanitized = sanitized.replace(".", "-").replace("--", "-")
    parts = [part for part in sanitized.split("-") if part]
    if len(parts) == 3:
        year, month, day = parts
        return f"{year.zfill(4)}-{month.zfill(2)}-{day.zfill(2)}"
    return None


def extract_text_lines(raw: Iterable[Sequence]) -> List[str]:
    """Return human-readable OCR lines for debugging and inspection."""

    return [line.text for line in _iter_detections(raw)]
