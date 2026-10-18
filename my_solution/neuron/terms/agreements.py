"""An individual agreement (NRAGRE) replaces the tariff rate of a policy while it is valid: an agreed entry charge
(ENT) or management charge (AMC). An agreed rate of 0 is still an agreement. The tariff rate is only looked up
without one: `tariff_rate(*args)`."""


def agreed_rate(agreed, tariff_rate, *args):
    return tariff_rate(*args) if agreed is None else agreed
