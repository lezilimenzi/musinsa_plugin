import pipeline
from pipeline import generate_reports, validate


def _plan():
    return [{
        "slot": 1, "category": "여름 페스티벌", "display_keyword": "워터 페스티벌룩",
        "look_id": "L003", "look_title": "블루 워터 페스티벌룩", "image_url": "https://x/L003.jpg",
        "full_body_visible": "true", "source_ids": "LIVE001", "selection_reason": "테마 근거에 부합",
    }]


def _mappings():
    return [{
        "slot": 1, "look_id": "L003", "display_keyword": "워터 페스티벌룩", "mapping_type": "core",
        "product_id": "P005", "product_name": "블루 그래픽 티셔츠", "category": "top", "reason": "룩에 직접 연결된 상품",
    }]


def _sources():
    return {"results": [{"source_id": "LIVE001", "title": "여름 트렌드", "url": "https://example.com/a"}]}


def test_reports_are_grounded(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "REPORTS", tmp_path)
    generate_reports(_plan(), _mappings(), _sources(), {"여름 페스티벌": 1})
    cards = (tmp_path / "look_first_cards.md").read_text(encoding="utf-8")
    assert "워터 페스티벌룩" in cards
    assert "전신 코디" in cards
    assert "LIVE001" in cards


def test_validate_passes_on_grounded_full_body_plan(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "REPORTS", tmp_path)
    generate_reports(_plan(), _mappings(), _sources(), {"여름 페스티벌": 1})
    result = validate(_plan(), {"target_slots": 1, "per_theme_cap": 3})
    assert result["status"] == "PASS"
    assert result["keyword_coverage"] == 1.0
    assert result["full_body_look_coverage"] == 1.0


def test_live_mode_requires_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    try:
        pipeline.live_search("2026-07-06")
    except RuntimeError as exc:
        assert "OPENAI_API_KEY" in str(exc)
    else:
        raise AssertionError("live mode should reject a missing API key")
