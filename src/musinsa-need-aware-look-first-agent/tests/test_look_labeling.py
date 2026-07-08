from pipeline import label_looks


def test_human_review_increases_confidence():
    looks = {row["look_id"]: row for row in label_looks()}
    assert float(looks["L001"]["label_confidence"]) > float(looks["L002"]["label_confidence"])
    assert "human" in looks["L001"]["label_sources"]


def test_sample_looks_expose_full_body_metadata():
    looks = label_looks()
    assert all(row["shot_type"] == "full_body" for row in looks)
    assert all(row["full_body_visible"] == "true" for row in looks)

