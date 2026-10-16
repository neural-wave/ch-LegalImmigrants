"""t0: broker commission of every counted premium item (99.996 % on the train targets).

Rules found:
- commission = amount received x rate(broker tier, premium type), rounded half up to the cent;
- the broker comes from the policy version valid on the day the money was received;
- the premium type (L regular / E single) is position 6 of the tariff key;
- items without money received and items whose booking event was reversed (type 900) are not counted.
"""
from decimal import ROUND_HALF_UP, Decimal

from dates import day
from loader import by_key, number, table
from params import broker_tier, commission_rate, policy_version, policy_versions

CENT = Decimal("0.01")


def reversed_events(legacy_dir):
    """{(policy, event)} cancelled by a reversal: a type 900 event names the event it cancels in EV_REVNR."""
    return {(e["EV_POLNR"], e["EV_REVNR"]) for e in table(legacy_dir, "NREVNT") if e["EV_EVTTP"] == "900"}


def commission(legacy_dir, item, premium_type):
    """Commission of one premium item."""
    policy, received = item["PR_POLNR"], day(item["PR_RCVDT"])
    # money received in a gap between two versions: the latest version applies
    version = policy_version(legacy_dir, policy, received) or policy_versions(legacy_dir, policy)[-1]
    rate = commission_rate(legacy_dir, broker_tier(legacy_dir, version["PH_BRKNR"]), premium_type, received)
    return (number(item["PR_AMTRC"], 2) * rate).quantize(CENT, ROUND_HALF_UP)


def solve(legacy_dir):
    """{(policy_id, due_nr): commission}"""
    premium_type = {p: r["RK_TARKEY"][5] for p, r in by_key(legacy_dir, "NRRISK", "RK_POLNR").items()}
    cancelled = reversed_events(legacy_dir)
    out = {}
    for item in table(legacy_dir, "NRPREM"):
        policy = item["PR_POLNR"]
        if int(item["PR_AMTRC"]) <= 0 or (policy, item["PR_EVTNR"]) in cancelled:
            continue
        out[(policy, int(item["PR_DUENR"]))] = commission(legacy_dir, item, premium_type[policy])
    return out
