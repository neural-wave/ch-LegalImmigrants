"""What a booking adds to the annual statement (t4), and in which column: a monthly charge (ADM, AMC, RSK) its amount,
a premium's fund booking (PRM) its entry charge (ENT), in the year of the trade date. Customer orders add nothing."""
from neuron.data import CHARGES, PREMIUM


def statement_entry(row):
    if row.kind in CHARGES:
        return row.kind, row.amount
    return ("ENT", row.entry_charge) if row.kind == PREMIUM else None
