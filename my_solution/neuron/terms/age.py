"""The insured's age in the policy year of a date: the entry age (rates.py), one more on every policy anniversary
(policy_years.py). The fund accounting reads the death probability at this age for every charge run."""
from neuron.calendar.policy_years import policy_years
from neuron.data import day
from neuron.terms.rates import entry_age


def age(policy, legacy_date):
    return entry_age(policy) + policy_years(policy.start, day(legacy_date))
