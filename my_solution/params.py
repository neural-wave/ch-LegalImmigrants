"""Parameter lookups "as of a date" in the versioned and validity-period tables of Neuron.

SCHEMA.md: the row valid on d has VLDFR <= d <= VLDTO (both inclusive); of several valid rows the highest
version wins. Rates N(6) are returned as Decimal fractions (12500 -> 0.0125).
"""
import functools

from dates import OPEN_END, day
from loader import by_key, grouped, number, table


def valid_on(rows, prefix, date):
    """Rows whose `<prefix>VLDFR .. <prefix>VLDTO` period contains `date`, in their original order.

    A VLDTO of `0` is treated like an open end.
    """
    return [r for r in rows if day(r[prefix + "VLDFR"]) <= date <= (day(r[prefix + "VLDTO"]) or OPEN_END)]


@functools.lru_cache(maxsize=None)
def policy_versions(legacy_dir, policy):
    """NRPOLH rows of a policy in ascending version number (cached: t0 asks for every premium item)."""
    return sorted(grouped(legacy_dir, "NRPOLH", "PH_POLNR")[policy], key=lambda r: int(r["PH_VRSNR"]))


def policy_version(legacy_dir, policy, date):
    """The highest policy version valid on `date`, or None if no version covers it.

    Version periods can leave gaps; callers decide what a gap means for them.
    """
    return (valid_on(policy_versions(legacy_dir, policy), "PH_", date) or [None])[-1]


def first_version(legacy_dir, policy):
    """Version 1 of the policy: the broker, premium and dates of the original application (the offer)."""
    return policy_versions(legacy_dir, policy)[0]


def broker_tier(legacy_dir, broker):
    """Tier A/B/C of a broker (NRBROK); it selects the entry charge and the commission rate."""
    return by_key(legacy_dir, "NRBROK", "BR_BRKNR")[broker]["BR_TIER"]


def charges(legacy_dir, family, generation, date):
    """NRCHRG row of a tariff family/generation valid on `date`.

    Before the first period of a generation Neuron used that generation's first row.
    """
    rows = [r for r in table(legacy_dir, "NRCHRG") if (r["CG_TARFAM"], r["CG_TARGEN"]) == (family, generation)]
    return (valid_on(rows, "CG_", date) or rows[:1])[-1]  # [:1]: applied for before the first period


def entry_rate(legacy_dir, tier, date):
    """Entry charge rate of a broker tier valid on `date` (NRENTC; tier B dropped to 3 % on 2021-07-01)."""
    rows = [r for r in table(legacy_dir, "NRENTC") if r["EC_TIER"] == tier]
    return number(valid_on(rows, "EC_", date)[-1]["EC_RATE"], 6)


@functools.lru_cache(maxsize=None)
def commission_rate(legacy_dir, tier, premium_type, date):
    """Commission rate of a broker tier and premium type (L regular / E single) valid on `date` (NRCOMR).

    Cached per (tier, type, date) because t0 looks it up for every premium item.
    """
    rows = [r for r in table(legacy_dir, "NRCOMR") if (r["CR_TIER"], r["CR_PAYTP"]) == (tier, premium_type)]
    return number(valid_on(rows, "CR_", date)[-1]["CR_RATE"], 6)


def illustration_rate(legacy_dir, date):
    """Growth rate p.a. of offers valid on `date` (NRILLU); t2 uses the application date."""
    return number(valid_on(table(legacy_dir, "NRILLU"), "IL_", date)[-1]["IL_RATE"], 6)


def agreed_rate(legacy_dir, policy, fee_type, date):
    """Individually agreed ENT/AMC rate of a policy valid on `date`, or None (NRAGRE).

    While an agreement is valid its rate replaces the tariff rate (t3/t4 ask once per premium and charge run).
    """
    rows = [r for r in grouped(legacy_dir, "NRAGRE", "AG_POLNR").get(policy, []) if r["AG_FEETP"] == fee_type]
    return next((number(r["AG_RATE"], 6) for r in reversed(valid_on(rows, "AG_", date))), None)


def allocation(legacy_dir, policy, date):
    """{fund: share} of the allocation set valid on `date`, the highest AL_VRSNR winning (NRALLO).

    The shares of a set add up to 1; prepared for t3/t4.
    """
    rows = valid_on(grouped(legacy_dir, "NRALLO", "AL_POLNR").get(policy, []), "AL_", date)
    top = max((int(r["AL_VRSNR"]) for r in rows), default=None)  # several sets can overlap, the newest wins
    return {r["AL_FNDID"]: number(r["AL_PCTG"], 6) for r in rows if int(r["AL_VRSNR"]) == top}
