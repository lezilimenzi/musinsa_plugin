from pipeline import label_looks, normalize_anchors, retrieve_candidates, sample_extract, sample_search, select_by_category
from common import load_structured
from pipeline import INPUTS


def _selection():
    config = load_structured(INPUTS / "home_context_config.yaml")
    anchors = normalize_anchors(sample_extract(sample_search(config["as_of"]), config["as_of"]))
    candidates = retrieve_candidates(anchors, label_looks(), config["minimum_label_confidence"])
    return select_by_category(candidates, config)


def test_selects_two_per_category_without_global_score():
    selected, actual = _selection()
    assert len(selected) == 10
    assert set(actual.values()) == {2}
    assert all("final_look_score" not in row for row in selected)


def test_requires_keyword_and_full_body():
    selected, _ = _selection()
    assert all(row["display_keyword"] for row in selected)
    assert all(row["full_body_visible"] == "true" for row in selected)


def test_selection_is_deterministic():
    first, _ = _selection()
    second, _ = _selection()
    assert [row["look_id"] for row in first] == [row["look_id"] for row in second]

