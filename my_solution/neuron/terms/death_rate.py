"""Yearly death probability of the insured at an age: the table's probability (rates.py) with the medical loading
RK_LOAD on top, x (1 + loading), and for smokers the tariff's smoker factor (smoker.py)."""
from neuron.data import num
from neuron.terms.rates import qx
from neuron.terms.smoker import smoker_factor


def death_rate(policy, tariff, age):
    return qx(policy, tariff, age) * (1 + num(policy.risk["RK_LOAD"], 6)) * smoker_factor(policy, tariff)
