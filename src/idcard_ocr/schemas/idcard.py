"""Pydantic schemas for ID card OCR API payloads."""
from __future__ import annotations

from pydantic import BaseModel, Field


class FieldSchema(BaseModel):
    value: str | None = Field(None, description="识别出的字段值，为空表示未识别到")
    confidence: float | None = Field(None, description="PaddleOCR 置信度，范围 0-1")


class FrontSideSchema(BaseModel):
    name: FieldSchema
    gender: FieldSchema
    ethnicity: FieldSchema
    birth_date: FieldSchema
    address: FieldSchema
    id_number: FieldSchema


class BackSideSchema(BaseModel):
    issuing_authority: FieldSchema
    valid_period: FieldSchema


class RawTextSchema(BaseModel):
    front: str = Field("", description="OCR 原始识别文本（正面，多行以换行拼接）")
    back: str = Field("", description="OCR 原始识别文本（反面，多行以换行拼接）")


class IdCardResponseSchema(BaseModel):
    front: FrontSideSchema
    back: BackSideSchema
    raw_text: RawTextSchema


class ErrorResponseSchema(BaseModel):
    detail: str
