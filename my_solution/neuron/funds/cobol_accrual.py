"""COBOL Neuron's management charge period: the days since the previous monthly anniversary over a 360-day year.
Anniversaries keep the start day where the month has it, so a policy started on the 31st was last charged on
31 January for the run of 29 February (29 days)."""
from decimal import Decimal

from neuron.calendar.months import add_months

YEAR_DAYS = 360


def cobol_accrual(policy, event):
    anniversary = policy.event_date(event)
    return Decimal((anniversary - add_months(anniversary, -1, policy.start.day)).days) / YEAR_DAYS
