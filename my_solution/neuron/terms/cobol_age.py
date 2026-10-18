"""COBOL Neuron's entry age: days since birth / 365, rounded. A year of 365 days, leap days counted, so the age turns
a few days before the half year, earlier for older people. An impossible birth date (31 November) counts as the
day after the 30th."""
import datetime as dt

DAYS = 365


def entry_age_cobol(birth, start):
    year, month, day = birth
    return round(((start - dt.date(year, month, 1)).days - day + 1) / DAYS)
