from src.modules.marketers.models import Address, Marketer


def test_marketer__str__(marketer: Marketer):
    assert marketer.__str__() == "Marketer: Marketer official"


def test_address__str__(address: Address):
    assert address.__str__() == "Address: Fifth Avenue 1, New York"
