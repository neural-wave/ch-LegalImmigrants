"""Neuron moves by whole calendar months (month_shift.py) and clamps to the month end: 31 January + 1 month = 28
February. The day of month can be given (`day_of_month`, a schedule's anchor day), else it is the date's own day.
Due dates, anniversaries and charge periods all count this way."""
import datetime as dt
from calendar import monthrange

from neuron.calendar.month_shift import month_shift


def add_months(d, months, day_of_month=None):
    year, month = month_shift(d, months)
    return dt.date(year, month, min(day_of_month or d.day, monthrange(year, month)[1]))
