"""Whole calendar months from one date to another, days ignored: 2016-08-01 -> 2041-08-01 is 300 months, the
length of the offer projection (t2) of a policy that starts on the first and matures 25 years later."""
from neuron.data import MONTHS


def months_between(start, end):
    return (end.year - start.year) * MONTHS + end.month - start.month
