"""t3 surrender value: full fund accounting of a policy and the amount paid on surrender.

The units come from the replayed bookings (neuron/funds/). On a valuation date the units traded up to that day are
valued at the last redemption price, in the policy currency, rounded per fund and pot. The surrender penalty of the
product's scale (NRSURR, by completed policy years) is deducted unless a waiver period (NRWAIV) covers the date.
Policies that ended by surrender or death are worth 0. COBOL Neuron (before the conversion) truncates the cents.
"""
import datetime as dt
import itertools
from decimal import Decimal

from neuron.data import as_of, guarded
from neuron.ended import has_ended
from neuron.funds.replay import accounts
from neuron.legacy import legacy
from neuron.terms.net_of_penalty import net_of_penalty
from neuron.valuation import pot_value


def policy_value(account, legacy_date):
    """Units x last redemption price in the policy currency, rounded per fund and pot.

    Each pot is valued and rounded on its own (neuron/valuation.py), at the bid of the valuation date; then added up.
    """
    holdings = account.holdings(legacy_date).items()
    return sum(pot_value(account.policy, fund, units, legacy_date, legacy_date) for (fund, _), units in holdings)


def surrender_value(account, version, legacy_date):
    """The policy value net of the surrender penalty; 0 once the policy ended (neuron/ended.py)."""
    return Decimal(0) if has_ended(version) else net_of_penalty(account.policy, legacy_date,
                                                                  policy_value(account, legacy_date))


def surrender_values(policy_id, account, valuation_dates):
    """[((policy_id, valuation_date), surrender_value)] of one policy, on the dates it is in force or has ended by.

    A policy without a version valid on a date has not started yet and has no row for it.
    """
    versions = {d: as_of(account.policy.versions, "PH", legacy(d)) for d in valuation_dates}
    return [((policy_id, d), surrender_value(account, v, legacy(d))) for d, v in versions.items() if v]


def t3_surrender_value(legacy_dir, valuation_dates: list[dt.date]) -> dict[tuple[str, dt.date], Decimal]:
    """{(policy_id, valuation_date): surrender_value}; policies with incomplete data are left out."""
    policies = accounts(legacy_dir).items()
    rows = (guarded(surrender_values, policy_id, account, valuation_dates) for policy_id, account in policies)
    return dict(itertools.chain.from_iterable(filter(None, rows)))
