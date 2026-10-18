"""Java Neuron's entry age: the age at the nearest birthday, from the whole months of age (months_of_age.py), rounding
up from 6 months after the birthday."""
from neuron.data import MONTHS
from neuron.terms.months_of_age import months_of_age


def entry_age_java(birth, start):
    return (months_of_age(birth, start) + MONTHS // 2) // MONTHS
