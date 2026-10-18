"""A premium counts once on the annual statement (t4), in the year of its money date, though its funds can trade on
different days: {premium event: money date} of the PRM bookings."""
from neuron.data import PREMIUM


def premium_dates(rows):
    return {r.event: r.money_date for r in rows if r.kind == PREMIUM}
