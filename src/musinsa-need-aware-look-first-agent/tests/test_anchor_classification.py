import pytest

from pipeline import normalize_anchors, sample_extract, sample_search


def test_sample_anchor_has_keyword_and_canonical_tags():
    signals = sample_extract(sample_search("2026-07-06"), "2026-07-06")
    anchors = normalize_anchors(signals)
    water = next(row for row in anchors if row["display_keyword"] == "워터 페스티벌룩")
    assert water["category"] == "event_tpo"
    assert "water_festival" in water["events"]
    assert "blue" in water["colors"]


def test_invalid_category_is_rejected():
    signal = {
        "signal_id": "SIG999", "source_id": "SRC999", "category": "unknown",
        "display_keyword": "테스트", "style_moods": [], "colors": [], "items": [],
        "materials": [], "events": [], "tpos": [], "weather": [], "seasons": [],
        "confidence": 0.5,
    }
    with pytest.raises(ValueError):
        normalize_anchors([signal])

