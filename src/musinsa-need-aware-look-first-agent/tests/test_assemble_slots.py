from collections import Counter

from pipeline import assemble_slots

LOOKS = [
    {"look_id": "L001", "look_title": "룩1", "image_url": "u1", "full_body_visible": "true", "linked_product_ids": "P001"},
    {"look_id": "L002", "look_title": "룩2", "image_url": "u2", "full_body_visible": "true", "linked_product_ids": "P002"},
    {"look_id": "L003", "look_title": "룩3", "image_url": "u3", "full_body_visible": "true", "linked_product_ids": "P003"},
]


def _pair(theme_id, theme_label, look_id, fit, kw="키워드", src="LIVE001"):
    return {"theme_id": theme_id, "theme_label": theme_label, "look_id": look_id,
            "display_keyword": kw, "fit_score": fit, "reason": "r", "evidence_source_ids": [src]}


def _ranked():
    # 같은 룩이 테마마다 다른 fit을 가짐 -> 전역 배정 검증용
    return [
        _pair("T1", "페스티벌", "L001", 0.9),
        _pair("T2", "오피스", "L001", 0.3),
        _pair("T1", "페스티벌", "L002", 0.5),
        _pair("T2", "오피스", "L002", 0.8),
        _pair("T1", "페스티벌", "L003", 0.2),
        _pair("T2", "오피스", "L003", 0.7),
    ]


def _by_look(plan):
    return {s["look_id"]: s["category"] for s in plan}


def test_no_duplicate_full_body_grounded():
    plan = assemble_slots(_ranked(), LOOKS, target_slots=10, per_theme_cap=3, min_fit_score=0.0)
    ids = [s["look_id"] for s in plan]
    assert len(ids) == len(set(ids))
    assert all(s["full_body_visible"] == "true" for s in plan)
    assert all(s["source_ids"] and s["display_keyword"] for s in plan)


def test_global_assignment_sends_look_to_best_theme():
    plan = assemble_slots(_ranked(), LOOKS, target_slots=10, per_theme_cap=3, min_fit_score=0.0)
    by = _by_look(plan)
    assert by["L001"] == "페스티벌"   # 0.9 > 0.3
    assert by["L002"] == "오피스"     # 0.8 > 0.5
    assert by["L003"] == "오피스"     # 0.7 > 0.2 (라운드로빈이면 페스티벌로 갈 수도 있었음)


def test_min_fit_score_drops_low_fits():
    plan = assemble_slots(_ranked(), LOOKS, target_slots=10, per_theme_cap=3, min_fit_score=0.6)
    assert len(plan) == 3  # 살아남는 쌍: 0.9 / 0.8 / 0.7
    assert all(s["look_id"] in {"L001", "L002", "L003"} for s in plan)


def test_does_not_force_target_when_floor_prunes():
    plan = assemble_slots(_ranked(), LOOKS, target_slots=10, per_theme_cap=3, min_fit_score=0.85)
    assert len(plan) == 1  # 0.9만 통과 -> 슬롯이 target보다 적어도 됨
    assert plan[0]["look_id"] == "L001"


def test_respects_per_theme_cap():
    plan = assemble_slots(_ranked(), LOOKS, target_slots=10, per_theme_cap=1, min_fit_score=0.0)
    counts = Counter(s["category"] for s in plan)
    assert all(count <= 1 for count in counts.values())


def test_respects_target_slots():
    plan = assemble_slots(_ranked(), LOOKS, target_slots=2, per_theme_cap=3, min_fit_score=0.0)
    assert len(plan) == 2


def test_slots_ordered_by_fit_desc():
    plan = assemble_slots(_ranked(), LOOKS, target_slots=10, per_theme_cap=3, min_fit_score=0.0)
    assert [s["look_id"] for s in plan] == ["L001", "L002", "L003"]  # 0.9, 0.8, 0.7
