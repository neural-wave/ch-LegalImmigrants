"""Neuron's trade order: by trade date, the charge run first on its day (it values the pots as they stood before
the other trades of the day), then as booked. A trade is one event on one trade date: the funds of one premium can
trade on different days, with a charge run in between."""
from neuron.data import CHARGES


def trade_order(rows):
    return rows[0].trade_date, rows[0].kind not in CHARGES, rows[0].book_id
