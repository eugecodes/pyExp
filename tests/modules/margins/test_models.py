from src.modules.margins.models import Margin


def test_margin__str__ok(margin: Margin):
    assert margin.__str__() == "Margin: consume_range for rate_id 2"
