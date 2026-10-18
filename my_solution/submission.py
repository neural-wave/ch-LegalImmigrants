"""Submission of the Neuron migration challenge.

Each task lives in its own module under `tasks/`; shared, deterministic building blocks live in `neuron/`.
Every value is calculated from `legacy_dir`. Only t5 reads `targets_dir`, as the challenge allows.
"""
from tasks.t0_commission import t0_commission
from tasks.t1_next_due_dates import t1_next_due_dates
from tasks.t2_projected_maturity_value import t2_projected_maturity_value
from tasks.t3_surrender_value import t3_surrender_value
from tasks.t4_annual_statement import t4_annual_statement
from tasks.t5_outlier_detection import t5_outlier_detection
from tasks.t7_tax import t7_tax_annual, t7_tax_payout

__all__ = [
    "t0_commission",
    "t1_next_due_dates",
    "t2_projected_maturity_value",
    "t3_surrender_value",
    "t4_annual_statement",
    "t5_outlier_detection",
    "t7_tax_payout",
    "t7_tax_annual",
]
