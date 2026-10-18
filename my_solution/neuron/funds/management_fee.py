"""The management charge (AMC) of a pot in a run: value before the run x yearly rate (rates.py) x period (accrual.py),
rounded to the cent in the era of the run. Not capped: it may leave a pot a cent short."""


def management_fee(value, rate, period, cents):
    return cents(value * rate * period)
