"""Unit bookings (NRBOOK), streamed one policy at a time, with the blank PRM columns recomputed (premiums.py).

Rules found:
- bookings of an event cancelled by a reversal (type 900 names it in EV_REVNR) and bookings of technical
  corrections (type 990) do not count;
- the booking type says what is known: customer orders (SWI, SWO, WDR, SUR, DTH) carry their units in
  BK_UNITS; PRM, ADM, AMC and RSK were calculated by a nightly job that is not in the extract;
- NRBOOK is written policy by policy in booking-id order, so it is streamed once (6.8 million rows) and only
  the compact records of the current policy are in memory.
"""
import collections
import csv
import functools
import pathlib

import dates
import premiums
from loader import number, table

CHARGES = ("ADM", "AMC", "RSK")
# one booking: id, event, type, fund, pot, trade date, price date, units (None for charges), and for PRM
# bookings the invested amount and the entry charge (None otherwise)
Booking = collections.namedtuple("Booking", "id event kind fund pot traded priced units invested entry")
day = functools.lru_cache(maxsize=None)(dates.day)  # a few thousand distinct dates in 6.8 million rows


@functools.lru_cache(maxsize=None)
def counted_events(legacy_dir):
    """{(policy, event): counts?}: an event counts unless it is a 990 correction or was reversed by a 900."""
    events = table(legacy_dir, "NREVNT")
    cancelled = {(e["EV_POLNR"], e["EV_REVNR"]) for e in events if e["EV_EVTTP"] == "900"}
    return {(e["EV_POLNR"], e["EV_EVTNR"]): e["EV_EVTTP"] != "990" and (e["EV_POLNR"], e["EV_EVTNR"]) not in cancelled
            for e in events}


def booking(legacy_dir, policy, row):
    """Booking record of one NRBOOK line (`row`: the raw fields in file order)."""
    kind, fund, traded, priced = row[5], row[3], day(row[7]), day(row[8])
    invested = units = entry = None
    if kind == "PRM":
        # premium: amount, units and entry charge as of the money date BK_RCVDT
        invested, units, entry = premiums.invest(legacy_dir, policy, row[2], fund, day(row[6]), traded, priced)
    elif kind not in CHARGES and row[12]:
        # customer order: the units Neuron booked
        units = number(row[12], 6)
    return Booking(int(row[0]), row[2], kind, fund, row[4], traded, priced, units, invested, entry)


def stream(legacy_dir):
    """Yields (policy, [Booking]) for every policy in file order, counted bookings only."""
    counted, current, rows = counted_events(legacy_dir), None, []
    with open(pathlib.Path(legacy_dir) / "NRBOOK.csv", encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter=";")
        next(reader)  # header: BK_BOOKID;BK_POLNR;BK_EVTNR;BK_FNDID;BK_POTCD;BK_BKTYP;BK_RCVDT;BK_TRDDT;...
        for row in reader:
            policy = row[1].strip()
            if policy != current:
                # a new policy block starts: hand over the finished one
                if rows:
                    yield current, rows
                current, rows = policy, []
            if counted.get((policy, row[2]), False):
                rows.append(booking(legacy_dir, policy, row))
    if rows:
        yield current, rows
