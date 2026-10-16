"""Read the Neuron extract: `;`-separated CSV files with blank-padded C columns and N(s) integer amounts.

Every table is read once per (legacy_dir, table) and kept in memory. Nothing is written to disk and the
`targets/` folder is never read.
"""
import csv
import functools
import pathlib
from decimal import Decimal


@functools.lru_cache(maxsize=None)
def table(legacy_dir, name):
    """All rows of `<legacy_dir>/<name>.csv` as dicts with trimmed fields.

    C columns are padded with blanks on the right ('BL10000001  '), so every field is stripped once here.
    """
    path = pathlib.Path(legacy_dir) / f"{name}.csv"
    with open(path, encoding="utf-8", newline="") as f:
        return [{k: v.strip() for k, v in row.items()} for row in csv.DictReader(f, delimiter=";")]


@functools.lru_cache(maxsize=None)
def by_key(legacy_dir, name, column):
    """{key: row} for a table whose `column` is unique (NRRISK, NRPERS, NRBROK, NRPROD).

    Cached like `table`, so the index is built once per folder.
    """
    return {row[column]: row for row in table(legacy_dir, name)}


@functools.lru_cache(maxsize=None)
def grouped(legacy_dir, name, column):
    """{key: [rows]} in file order, e.g. the versions of a policy or its premium items.

    Cached like `table`, so the grouping is built once per folder.
    """
    out = {}
    for row in table(legacy_dir, name):
        out.setdefault(row[column], []).append(row)
    return out


def number(value, decimals=0):
    """N(s) column: integer text with `decimals` implied decimals, ('123456', 2) -> Decimal('1234.56').

    An empty field means no value and is read as 0. Amounts are never converted through float.
    """
    return Decimal(value or 0).scaleb(-decimals)
