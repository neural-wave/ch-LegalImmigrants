"""The units a charge cancels in a pot: the charge (policy currency) converted at the FX of the trade date and
divided by the bid price, rounded to 6 decimals in the era of the run (`units`); negative, as the units leave the pot."""


def cancelled_units(amount, fx, price, units):
    return -units(amount * fx / price)
