from collections import Counter

from pipeline import assemble_slots

THEMES = [
    {"theme_id": "T1", "theme_label": "여름 페스티벌", "member_signal_ids": ["SIG001"], "rationale": "r"},
    {"theme_id": "T2", "theme_label": "폭염 오피스", "member_signal_ids": ["SIG002"], "rationale": "r"},
]
LOOKS = [
    {"look_id": "L001", "look_title": "룩1", "image_url": "u1", "full_body_visible": "true", "linked_product_ids": "P001"},
    {"look_id": "L002", "look_title": "룩2", "image_url": "u2", "full_body_visible": "true", "linked_product_ids": "P002"},
    {"look_id": "L003", "look_title": "룩3", "image_url": "u3", "full_body_visible": "true", "linked_product_ids": "P003"},
]


def _ranked():
    return [
        {"theme_id": "T1", "theme_label": "여름 페스티벌", "look_id": "L001", "display_keyword": "페스티벌룩", "fit_score": 0.9, "reason": "r", "evidence_source_ids": ["LIVE001"]},
        {"theme_id": "T1", "theme_label": "여름 페스티벌", "look_id": "L002", "display_keyword": "물놀이룩", "fit_score": 0.8, "reason": "r", "evidence_source_ids": ["LIVE001"]},
        {"theme_id": "T2", "theme_label": "폭염 오피스", "look_id": "L003", "display_keyword": "린넨룩", "fit_score": 0.7, "reason": "r", "evidence_source_ids": ["LIVE002"]},
    ]


def test_no_duplicate_full_body_and_grounded():
    plan = assemble_slots(_ranked(), THEMES, LOOKS, target_slots=10, per_theme_cap=3)
    look_ids = [s["look_id"] for s in plan]
    assert len(look_ids) == len(set(look_ids))
    assert all(s["full_body_visible"] == "true" for s in plan)
    assert all(s["source_ids"] for s in plan)
    assert all(s["display_keyword"] for s in plan)


def test_fills_what_it_can_when_short():
    plan = assemble_slots(_ranked(), THEMES, LOOKS, target_slots=10, per_theme_cap=3)
    assert len(plan) == 3  # only 3 distinct looks available
    assert [s["slot"] for s in plan] == [1, 2, 3]


def test_respects_target_slots():
    plan = assemble_slots(_ranked(), THEMES, LOOKS, target_slots=2, per_theme_cap=3)
    assert len(plan) == 2


def test_respects_per_theme_cap():
    plan = assemble_slots(_ranked(), THEMES, LOOKS, target_slots=10, per_theme_cap=1)
    counts = Counter(s["category"] for s in plan)
    assert all(count <= 1 for count in counts.values())


def test_round_robin_spreads_across_themes():
    plan = assemble_slots(_ranked(), THEMES, LOOKS, target_slots=2, per_theme_cap=3)
    assert {s["category"] for s in plan} == {"여름 페스티벌", "폭염 오피스"}
