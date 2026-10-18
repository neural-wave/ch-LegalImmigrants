"""The insured's age in month `month` of the offer projection: the entry age at the start date (terms/rates.py), one more
after every 12 months, as the offer counts policy years from the start."""
from neuron.data import MONTHS
from neuron.terms.rates import entry_age


def offer_age(policy, month):
    return entry_age(policy) + month // MONTHS
