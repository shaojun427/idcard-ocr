from io import BytesIO

from fastapi.testclient import TestClient

from importlib import import_module

from idcard_ocr.api.app import app
from idcard_ocr.inference.models import BackSideResult, FieldResult, FrontSideResult, IdCardResult


def test_parse_id_card_endpoint(monkeypatch):
    client = TestClient(app)

    fake_result = IdCardResult(
        front=FrontSideResult(
            name=FieldResult("张三", 0.99),
            gender=FieldResult("男", 0.95),
            ethnicity=FieldResult("汉", 0.92),
            birth_date=FieldResult("1990-01-01", 0.9),
            address=FieldResult("北京市朝阳区", 0.85),
            id_number=FieldResult("110101199001011234", 0.97),
        ),
        back=BackSideResult(
            issuing_authority=FieldResult("北京市公安局", 0.88),
            valid_period=FieldResult("2010.01.01-2030.01.01", 0.8),
        ),
    )

    def _fake_analyze(front: bytes, back: bytes):  # noqa: ANN001 - test helper
        return fake_result, ["姓名 张三", "性别 男"], ["签发机关 北京市公安局"]

    app_module = import_module("idcard_ocr.api.app")
    monkeypatch.setattr(app_module, "analyze_id_card", _fake_analyze)

    files = {
        "front_image": ("front.jpg", BytesIO(b"fakefront"), "image/jpeg"),
        "back_image": ("back.jpg", BytesIO(b"fakeback"), "image/jpeg"),
    }

    response = client.post("/api/v1/idcard/parse", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["front"]["name"]["value"] == "张三"
    assert data["back"]["valid_period"]["value"] == "2010.01.01-2030.01.01"
    assert "姓名 张三" in data["raw_text"]["front"]
