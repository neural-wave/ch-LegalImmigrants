"""Versioned parameter tables: the row valid on a legacy date d has VLDFR <= d <= VLDTO, and of several valid
rows the highest version number VRSNR wins (SCHEMA.md). Works for every table with validity columns, e.g.
as_of(versions, "PH", d) or as_of(rates, "CR", d); None when no row is valid."""


def as_of(rows, prefix, legacy_date):
    d = int(legacy_date)
    valid = [r for r in rows if int(r[f"{prefix}_VLDFR"]) <= d <= int(r[f"{prefix}_VLDTO"])]
    return max(valid, key=lambda r: int(r.get(f"{prefix}_VRSNR") or 0), default=None)
