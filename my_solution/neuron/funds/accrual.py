"""Part of the yearly management charge one monthly run takes: a twelfth in Java Neuron, the days since the
previous run over 360 in COBOL Neuron (cobol_accrual.py), by the era of the run's trade date."""
from decimal import Decimal

from neuron.data import MONTHS
from neuron.funds.cobol_accrual import cobol_accrual


def accrual(policy, event, cobol):
    return cobol_accrual(policy, event) if cobol else Decimal(1) / MONTHS
