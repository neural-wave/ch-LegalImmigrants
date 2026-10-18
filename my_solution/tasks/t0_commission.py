"""t0 commission: what the broker earns on every paid premium item.

Commission = received premium x rate of (broker tier, premium type), rounded half up to the cent (neuron/commission.py).
Broker and rate are those valid on the money date PR_RCVDT, so a broker change or a new rate counts from the first
premium received after it. Only paid items (PR_STATE P) earn one: returned, open and written-off items never do.
"""
import functools
from decimal import Decimal

from neuron.data import as_of, grouped, guarded, num, table
from neuron.terms.commission import commission

PAID = "P"  # NRCODE PRSTATE
PREMIUM_TYPE = {"E": "E"}  # a single premium (PH_FREQ E) has its own rates; every other frequency is regular (L)


@functools.cache
def commission_rates(legacy_dir):
    """NRCOMR rows per (broker tier, premium type), each kept with its validity versions."""
    index = {}
    for rate in table(legacy_dir, "NRCOMR"):
        index.setdefault((rate["CR_TIER"], rate["CR_PAYTP"]), []).append(rate)
    return index


def item_commission(legacy_dir, item):
    """((policy_id, due_nr), commission) of one paid premium item."""
    paid, policy_id = item["PR_RCVDT"], item["PR_POLNR"].strip()
    policy = as_of(grouped(legacy_dir, "NRPOLH", "PH_POLNR")[policy_id], "PH", paid)
    tier = grouped(legacy_dir, "NRBROK", "BR_BRKNR")[policy["PH_BRKNR"].strip()][0]["BR_TIER"]
    rates = commission_rates(legacy_dir)[tier, PREMIUM_TYPE.get(policy["PH_FREQ"], "L")]
    rate = num(as_of(rates, "CR", paid)["CR_RATE"], 6)
    return (policy_id, int(item["PR_DUENR"])), commission(num(item["PR_AMTRC"], 2), rate)


def t0_commission(legacy_dir) -> dict[tuple[str, int], Decimal]:
    """{(policy_id, due_nr): commission} of the paid premium items; items with incomplete data are left out."""
    paid = grouped(legacy_dir, "NRPREM", "PR_STATE").get(PAID, ())
    return dict(filter(None, (guarded(item_commission, legacy_dir, item) for item in paid)))
