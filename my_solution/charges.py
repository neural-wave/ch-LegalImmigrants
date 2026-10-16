"""The monthly charge run of a policy: one event with ADM (admin fee), AMC (management) and RSK (risk) bookings.

Rules found:
- the run values every fund/pot as units x bid price of the price date / fx of the trade date, to the cent,
  and books in the order ADM -> AMC -> RSK; units sold = amount x fx / bid to 6 decimals;
- ADM: the tariff's admin fee, split over ALL fund/pots of the run pro rata by value;
- AMC: per pot on its value before the run (formula in tariff.py);
- RSK: one risk charge on the value left after ADM and AMC (the cent values minus the amounts, formula in
  tariff.py), split like ADM;
- pro-rata shares are rounded one by one in the era of the run, the largest value absorbs the residual,
  and a share of 0.00 books nothing (a second row of the same pot books 0);
- a split never takes more than there is: an admin fee or risk charge above the value left is capped at it
  (every pot then pays exactly what it holds); the AMC is not capped, it may leave a pot a cent short.
"""
from decimal import Decimal

from market import CENT, UNIT, fx_ratio, price, rounded
from tariff import management_fee, risk_charge

ZERO = Decimal(0)


def split(total, values, date):
    """Pro-rata shares of `total` by `values`, each rounded to the cent; the largest value takes the residual."""
    base = sum(values, ZERO)
    if base <= 0:  # nothing to split over: no shares at all
        return [ZERO] * len(values)
    total = min(total, base)  # capped at what the pots hold
    shares = [rounded(total * v / base, CENT, date) for v in values]
    largest = max(range(len(values)), key=lambda i: values[i])
    shares[largest] = total - sum(shares, ZERO) + shares[largest]
    return shares


def quotes(legacy_dir, rows, currency):
    """{(fund, pot): (bid price of the price date, fx of the trade date)}, the first row of a pot winning."""
    out = {}
    for r in rows:
        out.setdefault((r.fund, r.pot), (price(legacy_dir, r.fund, r.priced), fx_ratio(legacy_dir, currency, r.fund, r.traded)))
    return out


def run(legacy_dir, rows, before, params, post):
    """Books one charge run: `rows` its bookings, `before` the holdings per (fund, pot), `post(row, amount, units)`
    records a booking. Pots without a holding are valued at 0 and still take part in the splits."""
    date, market = rows[0].traded, quotes(legacy_dir, rows, params.currency)
    # cent value of every pot before the run (a fund without price or fx is worth 0)
    values = {k: rounded(before.get(k, ZERO) * bid / fx, CENT, date) if bid and fx else ZERO for k, (bid, fx) in market.items()}
    taken = dict.fromkeys(market, ZERO)  # ADM + AMC amounts per pot, deducted before the risk charge

    def book(row, amount):
        bid, fx = market[(row.fund, row.pot)]
        # units sold for the amount, era rounding; nothing sold for 0.00
        post(row, amount, -rounded(amount * fx / bid, UNIT, date) if amount and bid and fx else ZERO)

    # 1. admin fee split over all pots by their value before the run
    shares = dict(zip(market, split(params.admin, list(values.values()), date)))
    for r in rows:
        if r.kind == "ADM":
            taken[(r.fund, r.pot)] += (amount := shares.pop((r.fund, r.pot), ZERO))
            book(r, amount)
    # 2. management charge per pot on the value before the run
    for r in rows:
        if r.kind == "AMC":
            rate = params.agreed if params.agreed is not None else (params.amc1 if r.pot == "1" else params.amc2)
            taken[(r.fund, r.pot)] += (amount := management_fee(values[(r.fund, r.pot)], rate, params.days, date))
            book(r, amount)
    # 3. risk charge on what is left, split like the admin fee
    if any(r.kind == "RSK" for r in rows):
        left = [values[k] - taken[k] for k in market]
        shares = dict(zip(market, split(risk_charge(sum(left, ZERO), params, date), left, date)))
        for r in rows:
            if r.kind == "RSK":
                book(r, shares.pop((r.fund, r.pot), ZERO))
