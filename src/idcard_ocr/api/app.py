"""FastAPI application entry point for the ID card OCR service."""
from __future__ import annotations

from dataclasses import asdict

from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

from idcard_ocr.inference.engine import PaddleOCRNotAvailable
from idcard_ocr.inference.service import analyze_id_card
from idcard_ocr.schemas.idcard import ErrorResponseSchema, IdCardResponseSchema

MAX_UPLOAD_SIZE = 8 * 1024 * 1024  # 8MB per image
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/jpg"}

app = FastAPI(title="ID Card OCR Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"], response_model=dict[str, str])
def health_check() -> dict[str, str]:
    """Basic liveness probe used by infrastructure and tests."""

    return {"status": "ok"}


@app.post(
    "/api/v1/idcard/parse",
    response_model=IdCardResponseSchema,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponseSchema},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponseSchema},
    },
    tags=["idcard"],
)
async def parse_id_card(
    front_image: UploadFile = File(..., description="身份证正面照片"),
    back_image: UploadFile = File(..., description="身份证反面照片"),
) -> IdCardResponseSchema:
    """Handle multipart uploads, invoke OCR, and return structured fields."""

    front_bytes = await _read_validated_file(front_image, "front_image")
    back_bytes = await _read_validated_file(back_image, "back_image")

    try:
        result, front_lines, back_lines = analyze_id_card(front_bytes, back_bytes)
    except PaddleOCRNotAvailable as exc:  # pragma: no cover - initialization failure
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    payload = {
        "front": asdict(result.front),
        "back": asdict(result.back),
        "raw_text": {
            "front": "\n".join(front_lines),
            "back": "\n".join(back_lines),
        },
    }
    return IdCardResponseSchema.model_validate(payload)


async def _read_validated_file(upload: UploadFile, field_name: str) -> bytes:
    content_type = (upload.content_type or "").lower()
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} must be a JPEG or PNG image",
        )
    data = await upload.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{field_name} is empty")
    if len(data) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} exceeds {MAX_UPLOAD_SIZE // (1024 * 1024)}MB limit",
        )
    return data
