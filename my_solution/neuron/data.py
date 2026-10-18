"""Shared access to the Neuron export: reading tables, indexing them and guarding against broken data.

Every task uses these helpers, so a decoding or history rule is fixed once for all tasks. The decoders of the legacy
formats are rule modules of their own, offered here too: day (cyymmdd.py), num (fixed_point.py), as_of (as_of.py).
The code values the rules branch on (premium frequencies, booking types) are defined here once.
"""
import csv
import datetime as dt
import functools
import gc
import pathlib
from decimal import InvalidOperation

from neuron.as_of import as_of
from neuron.cyymmdd import parts
from neuron.fixed_point import num

__all__ = ["BROKEN_DATA", "CHARGES", "FREQ_MONTHS", "MONTHS", "PREMIUM", "as_of", "day", "grouped", "guarded", "index",
           "num", "readable", "table"]
BROKEN_DATA = (KeyError, IndexError, ValueError, TypeError, InvalidOperation, AttributeError)  # a missing row, a
# malformed value, a short row (its missing cells are None)

# Premium frequencies (NRCODE domain FREQ) and the months between two due dates: monthly M, quarterly Q, half-yearly
# H and yearly J (German Jahr). A single premium (E, Einmal) has no next due date, so it is not in the table.
MONTHS = 12
FREQ_MONTHS = {"M": 1, "Q": 3, "H": 6, "J": 12}

# Booking types of NRBOOK (BK_BKTYP): a premium's fund booking PRM, the monthly charges ADM (admin fee), AMC
# (management) and RSK (risk), and the customer orders (switches SWO / SWI, withdrawal WDR, surrender SUR, death
# DTH), which carry their own units.
PREMIUM = "PRM"
CHARGES = ("ADM", "AMC", "RSK")


@functools.cache
def table(legacy_dir, name):
    """All rows of a legacy table as dicts (`;`-separated, see SCHEMA.md).

    Cached: all tasks run on the same export, so each file is parsed once. utf-8-sig drops a byte-order mark, which
    would otherwise stick to the first column name.
    """
    with open(pathlib.Path(legacy_dir, f"{name}.csv"), encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f, delimiter=";"))
    gc.freeze()  # the rows live for the whole run: the cyclic GC would re-scan millions of them again and again
    return rows


def guarded(compute, *args):
    """`compute(*args)`, or None when the export lacks a row it needs or holds a malformed value.

    Incomplete data of one policy (a missing broker, person or tariff row) must not stop the others: every task
    computes its policies or items through this and leaves out the ones that return None.
    """
    try:
        return compute(*args)
    except BROKEN_DATA:
        return None


def readable(decode, rows):
    """`decode(row)` of every row it can read. A malformed row of a shared table (a price, a rate, a mortality row)
    is left out, so it fails only the lookups that need it, not every policy of the export."""
    return filter(None, (guarded(decode, row) for row in rows))


@functools.cache
def grouped(legacy_dir, name, key_column):
    """Rows of a table grouped by one (trimmed) key column, e.g. all NRPOLH versions per policy.

    The index that keeps every per-policy lookup linear instead of a scan of the whole table.
    """
    groups = {}
    for row in table(legacy_dir, name):
        groups.setdefault(row[key_column].strip(), []).append(row)
    return groups


@functools.cache
def index(legacy_dir, name, *columns):
    """Rows of a table per combination of key columns (the first one trimmed), in file order: e.g. NRCHRG per
    (tariff family, generation). Like `grouped`, for lookups on more than one column."""
    rows = {}
    for row in table(legacy_dir, name):
        rows.setdefault((row[columns[0]].strip(), *(row[c] for c in columns[1:])), []).append(row)
    return rows


def day(legacy_date):
    """Legacy date CYYMMDD as a date (`1250131` = 2025-01-31)."""
    return dt.date(*parts(legacy_date))
