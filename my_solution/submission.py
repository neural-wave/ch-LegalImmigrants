"""Submission of the Neuron migration challenge: one thin function per task, the rules live in t0.py .. t4.py.

Shared helpers: loader.py (cached CSV reader), dates.py (CYYMMDD, month arithmetic, COBOL/Java eras, Ticino
business days), params.py (parameter lookups as of a date), market.py (prices, fx), bookings.py / charges.py /
accounting.py (the fund accounting behind t3 and t4). Dates are `datetime.date`, amounts are `decimal.Decimal`;
standard library only.
"""
import datetime as dt
from decimal import Decimal

import t0
import t1
import t2
import t3
import t4


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
    return t3.solve(legacy_dir, valuation_dates)


def t4_annual_statement(legacy_dir) -> dict[tuple[str, int], tuple[Decimal, ...]]:
    """{(policy_id, year): (premiums, entry_charges, admin_fees, management_fees, risk_charges, total_charges)}"""
    return t4.solve(legacy_dir)


def t5_outlier_detection(legacy_dir, targets_dir) -> set[tuple[str, object]]:
    """{(task, key)} of the values that were changed by hand (the only function allowed to read targets)."""
    import t5  # rule residuals + shape checks + NREXCP, see t5.py
    rules = {"t0_commission": t0_commission, "t2_projected_maturity_value": t2_projected_maturity_value,
             "t3_surrender_value": t3_surrender_value, "t4_annual_statement": t4_annual_statement}
    return t5.solve(legacy_dir, targets_dir, rules)
