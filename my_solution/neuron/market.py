"""Market data: unit prices (NRFPRC) and exchange rates (NRFXRT), each the last one known on or before a date.

Both are published on weekdays only, so a trade on a weekend or holiday uses the last earlier one. Exchange rates are
CHF per unit of a currency (CHF itself is 1), so every pair of currencies is crossed via CHF.
"""
import functools

from neuron.cross_rate import cross_rate
from neuron.data import guarded, num, table
from neuron.on_or_before import last


def series(rows, key, date, published, value):
    """{key: (sorted dates, values)}, with upper-cased keys: a few exchange rates are exported as `usd`.

    A later publication replaces an earlier one: some fund prices were restated, FP_CHGTS tells which came last.
    A row without a readable key or date is left out. A malformed value is kept as None, so only the policies that
    trade on it fail (and guarded() leaves them out), not every policy of the export.
    """
    latest = {}
    for k, d, _, v in sorted(filter(None, (guarded(entry, r, key, date, published, value) for r in rows)),
                             key=lambda e: e[2]):
        latest.setdefault(k, {})[d] = v
    return {k: (sorted(v), [v[d] for d in sorted(v)]) for k, v in latest.items()}


def entry(row, key, date, published, value):
    """(key, date, publication, value or None) of one price or rate row."""
    return row[key].strip().upper(), int(row[date]), int(row[published]), guarded(value, row)


class Market:
    """Prices per fund and CHF rates per currency of an export, indexed once for bisect lookups.

    Bid is the redemption price (units sold or cancelled), ask the issue price (units bought).
    """

    def __init__(self, legacy_dir):
        self.prices = series(table(legacy_dir, "NRFPRC"), "FP_FNDID", "FP_PRCDT", "FP_CHGTS",
                             lambda r: (num(r["FP_BIDPR"], 6), num(r["FP_ASKPR"], 6)))
        self.rates = series(table(legacy_dir, "NRFXRT"), "FX_CCY", "FX_RATDT", "FX_RATDT",
                            lambda r: num(r["FX_RATE"], 6))
        self.currency = {r["FD_FNDID"].strip(): r["FD_CCY"] for r in table(legacy_dir, "NRFUND")}

    def bid(self, fund, legacy_date):
        """Redemption price: the monthly charges cancel units at it, and t3 values the holdings at it."""
        return last(self.prices[fund], legacy_date)[0]

    def ask(self, fund, legacy_date):
        """Issue price: premiums buy units at it."""
        return last(self.prices[fund], legacy_date)[1]

    def fx(self, policy_ccy, fund, legacy_date):
        """Fund currency per unit of the policy currency, crossed via CHF.

        Never rounded: Neuron converts with the full quotient and rounds only the resulting amount or units.
        """
        return cross_rate(last(self.rates[policy_ccy], legacy_date), last(self.rates[self.currency[fund]], legacy_date))


market = functools.cache(Market)  # the market data of an export, loaded once
