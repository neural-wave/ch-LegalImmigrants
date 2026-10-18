"""What a surrender pays: the policy value less the surrender penalty (rates.py), rounded once to the cent in
the era of the date, never below 0: a policy whose charges ate more than its value pays nothing back."""
from decimal import Decimal

from neuron.terms.rates import penalty_rate


def net_of_penalty(policy, legacy_date, policy_value):
    net = policy.cents(policy_value * (1 - penalty_rate(policy, legacy_date)), legacy_date)
    return max(net, Decimal(0))
