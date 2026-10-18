"""Whole months of age on a date, as Java Neuron counts them: a month counts once its day of month is reached, so
2025-01-01 is 5 months after a 2 July birthday. `birth` is the raw (year, month, day): some are impossible dates."""
from neuron.data import MONTHS


def months_of_age(birth, start):
    year, month, day = birth
    return (start.year - year) * MONTHS + start.month - month - (start.day < day)
