"""Prices and exchange rates are published on weekdays only, so the one that applies on a date is the last one on
or before it. `dated` is (sorted legacy dates, values); bisect finds the last date not after the given one. Before
the first publication there is none: IndexError, so guarded() leaves the policy out instead of using a later value."""
import bisect


def last(dated, legacy_date):
    dates, values = dated
    if i := bisect.bisect_right(dates, legacy_date):
        return values[i - 1]
    raise IndexError(f"nothing published on or before {legacy_date}")
