"""Completed policy years on a date: one more on every anniversary of the start date. An anniversary on a day the
month doesn't have falls on the month end, so a policy started on 29 February has its anniversary on 28 February.
The age of the insured and the surrender penalty go by these years."""
from neuron.calendar.months import add_months
from neuron.data import MONTHS


def policy_years(start, today):
    years = today.year - start.year
    return years - (add_months(start, MONTHS * years) > today)
