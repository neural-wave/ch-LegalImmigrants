"""The value of a pot in the policy currency: its units at the bid of the price date, converted at the FX of the
valuation date, rounded to the cent in the era of that date. Neuron values each fund and pot on its own like this,
for the monthly charges as for the surrender value."""
import functools


def pot_value(policy, fund, units, priced, legacy_date):
    price, fx = policy.market.bid(fund, priced), policy.market.fx(policy.currency, fund, legacy_date)
    return valued(units, price, fx, functools.partial(policy.cents, legacy_date=legacy_date))


def valued(units, price, fx, cents):
    """Units x bid / FX, rounded by `cents`: one pot's value once its fund's price and FX are known."""
    return cents(units * price / fx)
