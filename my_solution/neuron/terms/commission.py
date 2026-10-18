"""A broker's commission on one paid premium item (t0): the amount received times the rate of the broker's tier and
premium type, rounded half up to the cent whatever the era (commission was never truncated, not even by COBOL)."""
from neuron.contract import cents


def commission(received, rate):
    return cents(received * rate)
