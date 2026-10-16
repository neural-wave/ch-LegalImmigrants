"""Fund accounting: replays the bookings of every policy and keeps the unit holdings per fund and pot.

Rules found:
- bookings are processed in trade-date order; on the same day the charge run comes BEFORE customer orders and
  premiums (the run values yesterday's holdings); further ties follow the event and the booking id;
- the ADM/AMC/RSK rows of one event form one charge run (charges.py); the trade date of the previous run
  dates the COBOL management charge (tariff.py);
- the holdings of a fund/pot on a date are the units of all its bookings traded on or before that date.

The replay keeps, per policy, the units after every trade date (for t3) and the charge and entry-charge
amounts per calendar year (for t4) instead of the 6.8 million booking rows.
"""
import bisect
import collections
import functools
from decimal import Decimal

import bookings
import charges
import tariff

ZERO = Decimal(0)


class Ledger:
    """What the replay keeps: `history[policy][(fund, pot)] = (trade dates, units after that date)` and
    `yearly[(policy, year)][type]` = amounts of the year (PRM = entry charges, ADM, AMC, RSK)."""

    def __init__(self):
        self.history, self.yearly = {}, {}

    def holdings(self, policy, date):
        """{(fund, pot): units} on `date` (fund/pots without a booking up to then are left out)."""
        out = {}
        for key, (dates, units) in self.history.get(policy, {}).items():
            # the last trade date on or before `date` tells the units held
            if i := bisect.bisect_right(dates, date):
                out[key] = units[i - 1]
        return out

    def post(self, policy, holdings, row, amount, units):
        """Record one booking: update the holdings, the history of its trade date and the yearly amounts."""
        key = (row.fund, row.pot)
        holdings[key] = holdings.get(key, ZERO) + units
        dates, after = self.history.setdefault(policy, {}).setdefault(key, ([], []))
        # bookings arrive in trade-date order: one history entry per date, the state after its last booking
        if dates and dates[-1] == row.traded:
            after[-1] = holdings[key]
        else:
            dates.append(row.traded)
            after.append(holdings[key])
        # amounts by trade-date year: charge amounts, and for PRM bookings the entry charge
        if amount is not None:
            self.yearly.setdefault((policy, row.traded.year), collections.defaultdict(Decimal))[row.kind] += amount


def ordered(rows):
    """Processing order: trade date, charge run before customer orders, then event (by its first booking), id."""
    # an event is ranked by its first booking id, so a run keeps together even if its ids interleave
    first = {}
    for r in rows:
        first[r.event] = min(first.get(r.event, r.id), r.id)
    # False sorts before True: on one trade date the charge rows (kind in CHARGES) come first
    return sorted(rows, key=lambda r: (r.traded, r.kind not in bookings.CHARGES, first[r.event], r.id))


def replay(legacy_dir, policy, rows, ledger):
    """Replay the bookings of one policy into `ledger`."""
    holdings, block, previous = {}, [], None
    post = functools.partial(ledger.post, policy, holdings)

    def flush():
        # a complete charge run: value the holdings before it and book its charges
        nonlocal previous
        if block:
            params = tariff.parameters(legacy_dir, policy, block[0].traded, previous)
            charges.run(legacy_dir, block, dict(holdings), params, post)
            # the next run's COBOL management charge counts its days from this run
            previous = block[0].traded
            block.clear()

    for row in ordered(rows):
        if row.kind in bookings.CHARGES:
            # consecutive charge rows of one event belong to the same run; another event starts a new one
            if block and block[0].event != row.event:
                flush()
            block.append(row)
        else:
            # a premium or customer order ends the run before it, then adds its own units
            flush()
            if row.units is not None:  # customer orders without BK_UNITS change nothing
                post(row, row.entry, row.units)
    flush()


@functools.lru_cache(maxsize=None)
def ledger(legacy_dir):
    """The replayed ledger of every policy in `legacy_dir` (built once, shared by t3 and t4)."""
    out = Ledger()
    for policy, rows in bookings.stream(legacy_dir):
        replay(legacy_dir, policy, rows, out)
    return out
