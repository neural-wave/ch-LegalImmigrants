"""NRBOOK, the unit bookings: reading them policy by policy and grouping them into trades in Neuron's order.

The amounts and units of PRM, ADM, AMC and RSK bookings are blank in the export (premium.py and
charges.py calculate them); customer orders (SWO, SWI, WDR, SUR, DTH) carry their units.
"""
import csv
import itertools
import operator
import pathlib
from decimal import Decimal

from neuron.counted import counted
from neuron.data import guarded, num
from neuron.funds.trade_order import trade_order

# NRBOOK columns a Booking reads, in the order of its arguments
ZERO = Decimal(0)  # one shared zero: Decimals are immutable, and 6.8 million rows need one
COLUMNS = ("BK_BOOKID", "BK_EVTNR", "BK_FNDID", "BK_POTCD", "BK_BKTYP", "BK_RCVDT", "BK_TRDDT", "BK_PRCDT", "BK_UNITS")


class Booking:
    """One NRBOOK row, with slots: the train export alone has 6.8 million of them.

    Amount (policy currency), price and units are calculated (premium.py, charges.py) unless the export has them;
    the entry charge is the part of a premium this booking's fund didn't get (PRM only).
    """
    __slots__ = ("book_id", "event", "fund", "pot", "kind", "money_date", "trade_date", "price_date", "units",
                 "amount", "price", "entry_charge")

    def __init__(self, book_id, event, fund, pot, kind, money, trade, priced, units):
        self.pot, self.kind = pot, kind
        self.book_id, self.event, self.fund = int(book_id), int(event), fund.strip()
        self.money_date, self.trade_date, self.price_date = int(money), int(trade), int(priced)
        self.units = num(units, 6) if units else ZERO  # blank for PRM, ADM, AMC, RSK: the replay calculates them
        self.amount = self.price = self.entry_charge = ZERO

    @property
    def key(self):
        """Where the units are kept: (fund, pot)."""
        return self.fund, self.pot


def read_bookings(legacy_dir):
    """(policy_id, [Booking]) per policy, streamed; None instead of the list when a row of that policy is malformed.

    NRBOOK is exported policy by policy, so one policy's rows are together and the file is never held whole. Columns
    are found by name in the header, so an extra or reordered column changes nothing. Blank lines are skipped, and a
    malformed row costs only its own policy (guarded() in replay.py leaves a None out), not the rest of the file.
    """
    with open(pathlib.Path(legacy_dir, "NRBOOK.csv"), encoding="utf-8-sig") as f:
        rows = filter(None, csv.reader(f, delimiter=";"))
        header = next(rows)
        pick, policy = operator.itemgetter(*map(header.index, COLUMNS)), header.index("BK_POLNR")
        for policy_id, group in itertools.groupby(rows, key=lambda r: r[policy].strip()):
            yield policy_id, guarded(decoded, pick, group)


def decoded(pick, rows):
    """The Bookings of one policy's rows, decoded as they are read: a list of the raw rows would keep them alive and
    double the work of the cyclic GC. After a malformed row, groupby skips the rest of the policy's rows."""
    return [Booking(*pick(r)) for r in rows]


def trades(bookings, skipped):
    """The counted bookings (neuron/counted.py) grouped into trades, in the order Neuron traded them (trade_order.py).

    A trade is one event on one trade date: the funds of one premium can trade on different days.
    """
    grouped = {}
    for b in counted(bookings, skipped):
        grouped.setdefault((b.event, b.trade_date), []).append(b)
    return sorted(grouped.values(), key=trade_order)
