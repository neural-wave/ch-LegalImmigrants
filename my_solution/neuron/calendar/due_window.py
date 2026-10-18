"""The due dates t1 asks for: after the extract date and at most one year later (extract + 12 months, clamped to
the month end). The schedule itself already stops before maturity (due_dates.py)."""
from neuron.calendar.months import add_months


def upcoming(dues, extract_date):
    horizon = add_months(extract_date, 12)
    return [due for due in dues if extract_date < due <= horizon]
