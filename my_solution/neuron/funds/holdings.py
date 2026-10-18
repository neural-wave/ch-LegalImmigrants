"""The units of a pot on a valuation date: those after the last trade day on or before it (the day's last trade
counts), 0 for a pot first traded after the date. `after` is {trade date: units}, dates in trade order."""
import bisect
from decimal import Decimal


def units_on(after, legacy_date):
    dates = list(after)
    i = bisect.bisect_right(dates, legacy_date)
    return after[dates[i - 1]] if i else Decimal(0)
