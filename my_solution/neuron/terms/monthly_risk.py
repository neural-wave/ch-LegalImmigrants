"""One month of the risk charge, before rounding: the sum at risk (death_benefit.py) times a twelfth of the yearly
death probability (death_rate.py). The offer projection (t2) and the charge runs (t3, t4) both take it this way."""
from neuron.data import MONTHS
from neuron.terms.death_benefit import sum_at_risk


def monthly_risk(policy, value, death_rate):
    return sum_at_risk(policy, value) * death_rate / MONTHS
