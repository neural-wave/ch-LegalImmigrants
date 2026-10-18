"""A premium's booking in one fund: the fund's share of the invested premium, rounded on its own (no intermediate
rounding); its entry charge (t4) is its share of the whole premium, rounded, minus that amount; the units are the
amount x FX / ask price, 6 decimals. All rounded in the era of the trade date."""


def invest(policy, row, premium, invested, share, fx, traded):
    row.amount = policy.cents(invested * share, traded)
    row.entry_charge = policy.cents(premium * share, traded) - row.amount
    row.units = policy.units(row.amount * fx / row.price, traded)
