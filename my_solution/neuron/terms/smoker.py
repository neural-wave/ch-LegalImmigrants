"""Smokers pay more for the risk: their death probability is multiplied by the tariff's smoker factor CG_SMKFAC.
PS_SMOKE is J (Ja) or N (Nein); non-smokers keep the table's probability (factor 1)."""
from neuron.data import num

SMOKER = "J"


def smoker_factor(policy, tariff):
    return num(tariff["CG_SMKFAC"], 6) if policy.person["PS_SMOKE"] == SMOKER else 1
