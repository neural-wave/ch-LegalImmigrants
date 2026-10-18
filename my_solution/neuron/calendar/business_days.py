"""A due date on a weekend or a Ticino holiday is collected on the first business day after it (business_day.py);
one on a business day is collected that day."""
import datetime as dt

from neuron.calendar.business_day import is_business_day


def next_business_day(d):
    while not is_business_day(d):
        d += dt.timedelta(days=1)
    return d
