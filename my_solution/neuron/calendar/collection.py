"""When a premium is collected (t1): direct debits (PH_PAYMT LS, Lastschrift) on the first Ticino business day on
or after the due date (business_days.py); bank transfers (UB, Überweisung) are due as they are, even on a Sunday."""
from neuron.calendar.business_days import next_business_day

DIRECT_DEBIT = "LS"


def collection_date(due, payment_method):
    return next_business_day(due) if payment_method == DIRECT_DEBIT else due
