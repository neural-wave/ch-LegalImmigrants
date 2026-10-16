"""Submission of the Neuron migration challenge: one thin function per task, the rules live in t0.py, t1.py, t2.py.

Shared helpers: loader.py (cached CSV reader), dates.py (CYYMMDD, month arithmetic, COBOL/Java eras, Ticino
business days) and params.py (parameter lookups as of a date). Dates are `datetime.date`, amounts are
`decimal.Decimal`; standard library only.
"""
import datetime as dt
from decimal import Decimal

import t0
import t1
import t2


def t0_commission(legacy_dir) -> dict[tuple[str, int], Decimal]:
    """{(policy_id, due_nr): commission}"""
    return t0.solve(legacy_dir)


def t1_next_due_dates(legacy_dir, extract_date: dt.date) -> dict[tuple[str, int], tuple[dt.date, dt.date]]:
    """{(policy_id, n): (due_date, collection_date)} for the due dates after `extract_date`, n = 1, 2, ..."""
    return t1.solve(legacy_dir, extract_date)


def t2_projected_maturity_value(legacy_dir) -> dict[str, Decimal]:
    """{policy_id: maturity_value}"""
    return t2.solve(legacy_dir)


def t3_surrender_value(legacy_dir, valuation_dates: list[dt.date]) -> dict[tuple[str, dt.date], Decimal]:
    """{(policy_id, valuation_date): surrender_value}"""
    return {}  # TODO: unit holdings (NRBOOK/NRFPRC) and surrender scale (NRSURR/NRWAIV) not reconstructed yet


def t4_annual_statement(legacy_dir) -> dict[tuple[str, int], tuple[Decimal, ...]]:
    """{(policy_id, year): (premiums, entry_charges, admin_fees, management_fees, risk_charges, total_charges)}"""
    return {}  # TODO: calendar-year statement from the monthly charge run (event 300) not reconstructed yet


def t5_outlier_detection(legacy_dir, targets_dir) -> set[tuple[str, object]]:
    """{(task, key)} of the values that were changed by hand (the only function allowed to read targets)."""
    return set()  # TODO: compare the rule results with `targets_dir` once t3/t4 are in place
