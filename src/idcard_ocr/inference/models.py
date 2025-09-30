"""Dataclasses that capture structured OCR outputs for Chinese ID cards."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class FieldResult:
    """Holds a recognized value and the aggregate confidence score."""

    value: Optional[str]
    confidence: Optional[float]


@dataclass(slots=True)
class FrontSideResult:
    """Fields expected on the front (portrait) side of the ID card."""

    name: FieldResult
    gender: FieldResult
    ethnicity: FieldResult
    birth_date: FieldResult
    address: FieldResult
    id_number: FieldResult


@dataclass(slots=True)
class BackSideResult:
    """Fields expected on the back (emblem) side of the ID card."""

    issuing_authority: FieldResult
    valid_period: FieldResult


@dataclass(slots=True)
class IdCardResult:
    """Aggregates front and back recognition results."""

    front: FrontSideResult
    back: BackSideResult
