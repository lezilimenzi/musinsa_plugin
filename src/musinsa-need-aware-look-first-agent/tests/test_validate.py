import pipeline
from pipeline import validate

CONFIG = {"target_slots": 10, "per_theme_cap": 3}


def _plan(n=2, full_body="true", keyword="키워드", source="LIVE001"):
    return [
        {"slot": i + 1, "category": "테마", "display_keyword": keyword, "look_id": f"L00{i + 1}",
         "look_title": "t", "image_url": "u", "full_body_visible": full_body,
         "source_ids": source, "selection_reason": "r"}
        for i in range(n)
    ]


def test_pass_with_coverage_gap(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "REPORTS", tmp_path)
    res = validate(_plan(2), CONFIG)
    assert res["status"] == "PASS"
    assert res["coverage_gap"] == 8
    assert res["slot_count"] == 2


def test_empty_plan_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "REPORTS", tmp_path)
    res = validate([], CONFIG)
    assert res["status"] == "FAIL"
    assert "no slots generated" in res["errors"]


def test_non_full_body_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "REPORTS", tmp_path)
    res = validate(_plan(2, full_body="false"), CONFIG)
    assert res["status"] == "FAIL"


def test_missing_source_ids_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "REPORTS", tmp_path)
    res = validate(_plan(2, source=""), CONFIG)
    assert res["status"] == "FAIL"


def test_missing_keyword_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "REPORTS", tmp_path)
    res = validate(_plan(2, keyword=""), CONFIG)
    assert res["status"] == "FAIL"


def test_banned_claim_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "REPORTS", tmp_path)
    (tmp_path / "card.md").write_text("이 룩은 매출을 증가시킨다", encoding="utf-8")
    res = validate(_plan(2), CONFIG)
    assert res["status"] == "FAIL"


def test_duplicate_look_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "REPORTS", tmp_path)
    plan = _plan(2)
    plan[1]["look_id"] = plan[0]["look_id"]
    res = validate(plan, CONFIG)
    assert res["status"] == "FAIL"
