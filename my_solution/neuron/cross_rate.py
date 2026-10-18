"""Exchange rates are CHF per unit of a currency (CHF itself is 1), so fund currency per unit of policy currency is
the policy currency's CHF rate over the fund currency's. Never rounded: Neuron converts with the full quotient and
rounds only the resulting amount or units."""


def cross_rate(policy_rate, fund_rate):
    return policy_rate / fund_rate
