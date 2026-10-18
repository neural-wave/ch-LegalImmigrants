"""A business day of canton Ticino, on which direct debits (t1) are collected: Monday to Friday and not a public
holiday (holidays.py)."""
from neuron.calendar.holidays import holidays


def is_business_day(d):
    return d.weekday() < 5 and d not in holidays(d.year)
