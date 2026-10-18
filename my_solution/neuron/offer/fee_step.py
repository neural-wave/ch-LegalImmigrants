"""The offer projection's fees of one month: the tariff's admin fee out, then the management charge on what is left,
a twelfth of the yearly base-unit rate CG_AMCP2 (the offer has no initial units), rounded to the cent in the era of
the application date."""
from neuron.contract import cents
from neuron.data import MONTHS


def after_fees(value, admin_fee, management_rate, cobol):
    value -= admin_fee
    return value - cents(value * management_rate / MONTHS, cobol)
