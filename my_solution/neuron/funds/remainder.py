"""The rounding remainder of a split (`split`, replay.py): every share is rounded on its own, and the pot with the largest
value takes what is missing or left over, so the shares add up to the charge. On equal values the first pot takes
it, and pots with a booking row come first (BL10002262, December 2019)."""


def with_remainder(shares, values, charge):
    shares[max(values, key=values.get)] += charge - sum(shares.values())
    return shares
