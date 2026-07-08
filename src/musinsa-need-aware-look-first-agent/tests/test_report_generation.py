from pathlib import Path

import pipeline


def test_sample_pipeline_generates_grounded_reports(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "OUTPUTS", tmp_path / "outputs")
    monkeypatch.setattr(pipeline, "REPORTS", tmp_path / "reports")
    result = pipeline.run(mode="sample", clean_output=True)
    assert result["status"] == "PASS"
    assert result["keyword_coverage"] == 1.0
    assert result["full_body_look_coverage"] == 1.0
    cards = (tmp_path / "reports" / "look_first_cards.md").read_text(encoding="utf-8")
    assert "워터 페스티벌룩" in cards
    assert "전신 코디" in cards
    assert "SRC003" in cards


def test_live_mode_requires_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    try:
        pipeline.live_search("2026-07-06")
    except RuntimeError as exc:
        assert "OPENAI_API_KEY" in str(exc)
    else:
        raise AssertionError("live mode should reject a missing API key")

