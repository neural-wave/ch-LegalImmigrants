"""The offer projection's risk charge of one month: one month of risk (monthly_risk.py) on the value after the fees,
at the death probability of the insured's age that month (offer_age.py), rounded to the cent in the era of the
application date."""
from neuron.contract import cents
from neuron.terms.monthly_risk import monthly_risk


def after_risk(policy, value, death_rate, cobol):
    return value - cents(monthly_risk(policy, value, death_rate), cobol)
