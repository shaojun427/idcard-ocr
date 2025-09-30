from idcard_ocr.inference.models import BackSideResult, FieldResult, FrontSideResult, IdCardResult
from idcard_ocr.inference.parser import parse_id_card


def _detection(text: str, score: float = 0.9):
    return [[[0, 0], [1, 0], [1, 1], [0, 1]], (text, score)]


def test_parse_id_card_extracts_expected_fields():
    front_raw = [
        _detection("姓名张三"),
        _detection("性别男"),
        _detection("民族汉"),
        _detection("出生1990年01月01日"),
        _detection("住址北京市朝阳区幸福路1号"),
        _detection("公民身份号码110101199001011234"),
    ]
    back_raw = [
        _detection("签发机关北京市公安局"),
        _detection("有效期限2010.01.01-2030.01.01"),
    ]

    result = parse_id_card(front_raw, back_raw)

    assert result.front.name.value == "张三"
    assert result.front.gender.value == "男"
    assert result.front.ethnicity.value == "汉"
    assert result.front.birth_date.value == "1990-01-01"
    assert "北京市" in (result.front.address.value or "")
    assert result.front.id_number.value == "110101199001011234"

    assert result.back.issuing_authority.value == "北京市公安局"
    assert result.back.valid_period.value == "2010.01.01-2030.01.01"


def test_parse_id_card_handles_missing_fields_gracefully():
    front_raw = [_detection("姓名：李四"), _detection("公民身份号码：320000000000000000")]
    back_raw = []

    result = parse_id_card(front_raw, back_raw)

    assert result.front.name.value == "李四"
    assert result.front.gender.value is None
    assert result.back.issuing_authority.value is None


def test_parse_id_card_parses_combined_lines_and_compact_dates():
    front_raw = [
        _detection("性别男民族汉"),
        _detection("出生19900101"),
    ]
    back_raw = []

    result = parse_id_card(front_raw, back_raw)

    assert result.front.gender.value == "男"
    assert result.front.ethnicity.value == "汉"
    assert result.front.birth_date.value == "1990-01-01"


def test_parse_id_card_handles_verbose_birth_and_address_blocks():
    front_raw = [
        _detection("出生1990年1月1日"),
        _detection("住址"),
        _detection("江苏省南京市建邺区测试路123号"),
        _detection("公民身份号码110101199001012345"),
    ]
    back_raw = []

    result = parse_id_card(front_raw, back_raw)

    assert result.front.birth_date.value == "1990-01-01"
    assert result.front.address.value == "江苏省南京市建邺区测试路123号"
    assert result.front.id_number.value == "110101199001012345"


def test_parse_id_card_allows_noisy_ethnicity_label():
    front_raw = [
        _detection("姓名张三"),
        _detection("性别男"),
        _detection("民旅汉"),
    ]
    back_raw = []

    result = parse_id_card(front_raw, back_raw)

    assert result.front.ethnicity.value == "汉"


def test_parse_id_card_handles_split_birth_components():
    front_raw = [
        _detection("出生"),
        _detection("1990"),
        _detection("年01"),
        _detection("月01 日"),
    ]
    back_raw = []

    result = parse_id_card(front_raw, back_raw)

    assert result.front.birth_date.value == "1990-01-01"
