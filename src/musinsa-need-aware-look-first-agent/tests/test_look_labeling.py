from pipeline import label_looks


def test_label_confidence_from_products():
    looks = {row["look_id"]: row for row in label_looks()}
    # 연결 상품이 있는 룩은 base(0.75) + 0.05 = 0.80
    assert all(float(row["label_confidence"]) >= 0.75 for row in looks.values())
    assert all(row["label_sources"] == "metadata,products" for row in looks.values())


def test_sample_looks_expose_full_body_metadata():
    looks = label_looks()
    assert all(row["shot_type"] == "full_body" for row in looks)
    assert all(row["full_body_visible"] == "true" for row in looks)
