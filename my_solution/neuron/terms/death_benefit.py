"""The sum at risk: death benefit minus the value, by the death benefit option (tariff key position 7). A pays 101 %
of the value (1 % of it is at risk), B the higher of sum insured and value, C the value plus the sum insured."""
from decimal import Decimal

MARGIN = Decimal("0.01")


def sum_at_risk(policy, value):
    return {"A": value * MARGIN, "B": max(policy.sum_insured - value, 0), "C": policy.sum_insured}[policy.tariff[6]]
