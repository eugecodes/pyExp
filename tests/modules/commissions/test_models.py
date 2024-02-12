from src.modules.commissions.models import Commission


def test_commission__str__(commission: Commission):
    assert commission.__str__() == "Commission: Commission name"


def test_commission_properties(commission: Commission):
    assert commission.marketer_id == 1
    assert commission.rate_type__energy_type == "electricity"
    assert commission.rates__energy_type == "electricity"
    assert commission.price_type == "fixed_fixed"


def test_commission_fixed_base_properties(commission_fixed_base: Commission):
    assert commission_fixed_base.marketer_id == 1
    assert commission_fixed_base.rate_type__energy_type is None
    assert commission_fixed_base.rates__energy_type == "gas"
    assert commission_fixed_base.price_type == "fixed_base"


def test_commission_property_marketer_id_no_rates(commission: Commission):
    commission.rates = []

    assert commission.marketer_id is None


def test_commission_property_rate_type__energy_type_no_rate_type(
    commission: Commission,
):
    commission.rate_type = None

    assert commission.rate_type__energy_type is None


def test_commission_property_rates__energy_type_no_rates(commission: Commission):
    commission.rates = []

    assert commission.rates__energy_type is None


def test_commission_property_price_type_no_rates(commission: Commission):
    commission.rates = []

    assert commission.price_type is None
