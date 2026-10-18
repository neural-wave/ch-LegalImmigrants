"""All due dates of a premium schedule: the anchor (anchor.py) plus every `step` months on the anchor's day,
clamped to the month end, never on or after the maturity date `end`. Endless schedules are cut there."""
import itertools

from neuron.calendar.anchor import anchor
from neuron.calendar.months import add_months


def due_dates(start, step, conversion, end):
    first = anchor(start, step, conversion)
    dues = (add_months(first, months, first.day) for months in itertools.count(0, step))
    return itertools.takewhile(lambda due: due < end, dues)
