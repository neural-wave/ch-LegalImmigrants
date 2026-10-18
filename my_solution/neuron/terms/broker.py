"""The broker of a policy on a date: the one of the policy version valid on that date. An offer is signed before
the first version is valid, so on the application date it is the broker of the first version."""
from neuron.data import as_of


def broker(policy, legacy_date):
    return (as_of(policy.versions, "PH", legacy_date) or policy.first)["PH_BRKNR"].strip()
