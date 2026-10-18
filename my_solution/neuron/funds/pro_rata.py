"""Each pot's share of a charge in proportion to its value, charge x value / sum of the values, rounded to the cent
on its own in the era of the run (`split` in replay.py takes the remainder to the largest pot)."""


def pro_rata(charge, values, whole, cents):
    return {k: cents(charge * v / whole) for k, v in values.items()}
