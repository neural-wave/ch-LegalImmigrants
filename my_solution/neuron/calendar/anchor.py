"""The anchor of a premium schedule (t1). COBOL Neuron added the period to the previous due date, so a clamped
day stuck (31 -> 28 Feb -> 28 Mar). The conversion kept the first due date on or after it, with its day, as the
anchor of the Java schedule; a policy started after the conversion is anchored on its start date."""
from neuron.calendar.months import add_months


def anchor(start, step, conversion):
    while start < conversion:
        start = add_months(start, step)
    return start
