from pipeline import INPUTS
from common import load_structured


def test_category_quotas_are_two_each():
    config = load_structured(INPUTS / "home_context_config.yaml")
    assert set(config["quotas"].values()) == {2}
    assert sum(config["quotas"].values()) == config["slot_count"] == 10

