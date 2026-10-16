"""Market data of the fund accounting: unit prices (NRFPRC), exchange rates (NRFXRT) and era rounding.

Rules found:
- a price date can be published several times; the row with the latest FP_CHGTS counts;
- lookups are "last price on or before the date" (bid for valuations and charges, ask for premiums);
- NRFXRT holds CHF per unit of currency; the policy-to-fund ratio is rate(policy ccy) / rate(fund ccy),
  the currency code must be upper-cased before the lookup (the extract mixes 'usd' and 'USD');
- amounts in policy currency are kept to the cent, units to 6 decimals, with the rounding of the era.
"""
import bisect
import functools
from decimal import Decimal

from dates import day, rounding
from loader import by_key, number, table

CENT = Decimal("0.01")
UNIT = Decimal("0.000001")


def rounded(value, step, date):
    """`value` rounded to `step` (CENT or UNIT) the way the system in charge on `date` rounded."""
    return value.quantize(step, rounding(date))


def series(rows, date_column, columns, decimals):
    """{key: (dates, (values of column 1, ...))} sorted by date, for the as-of lookups.

    `rows` is {key: {date: row}}: the per-date dedupe has already happened in the caller.
    """
    out = {}
    for key, per_date in rows.items():
        dates = sorted(per_date)
        values = tuple([number(per_date[d][c], decimals) for d in dates] for c in columns)
        out[key] = (dates, values)
    return out


def as_of(entry, date, column=0):
    """Value of `column` at the last date <= `date`, or None when the series starts later."""
    dates, values = entry
    i = bisect.bisect_right(dates, date)
    return values[column][i - 1] if i else None


@functools.lru_cache(maxsize=None)
def prices(legacy_dir):
    """{fund: (dates, (bids, asks))}; of several publications per day the latest FP_CHGTS wins."""
    rows = {}
    for r in table(legacy_dir, "NRFPRC"):
        per_date = rows.setdefault(r["FP_FNDID"], {})
        d = day(r["FP_PRCDT"])
        if d not in per_date or r["FP_CHGTS"] > per_date[d]["FP_CHGTS"]:  # latest publication counts
            per_date[d] = r
    return series(rows, "FP_PRCDT", ("FP_BIDPR", "FP_ASKPR"), 6)


@functools.lru_cache(maxsize=None)
def fx_rates(legacy_dir):
    """{currency: (dates, (rates,))} with upper-cased currency codes; a repeated (ccy, date) keeps the last row."""
    rows = {}
    for r in table(legacy_dir, "NRFXRT"):
        rows.setdefault(r["FX_CCY"].upper(), {})[day(r["FX_RATDT"])] = r
    return series(rows, "FX_RATDT", ("FX_RATE",), 6)


@functools.lru_cache(maxsize=None)
def fund_currency(legacy_dir, fund):
    """Currency of a fund (NRFUND)."""
    return by_key(legacy_dir, "NRFUND", "FD_FNDID")[fund]["FD_CCY"]


def price(legacy_dir, fund, date, ask=False):
    """Last bid (or ask) price of `fund` on or before `date`, or None."""
    entry = prices(legacy_dir).get(fund)
    return as_of(entry, date, 1 if ask else 0) if entry else None


def fx_ratio(legacy_dir, policy_ccy, fund, date):
    """Fund currency per policy currency on `date`: rate(policy ccy) / rate(fund ccy), both as of `date`.

    Returns None if either currency has no rate yet (EUR exists from 1998-12-31).
    """
    rates = fx_rates(legacy_dir)
    policy_rate = as_of(rates[policy_ccy.upper()], date)
    fund_rate = as_of(rates[fund_currency(legacy_dir, fund).upper()], date)
    return policy_rate / fund_rate if policy_rate and fund_rate else None
