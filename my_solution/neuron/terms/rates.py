"""The rates of a policy on a date: tariff charges, individual agreements, entry charge, fund allocation, the
insured's mortality and age, and the surrender penalty.

Every rate comes from its parameter table as of the date of the booking (as_of). An individual agreement (NRAGRE)
replaces the tariff rate while it is valid (agreements.py).

The offer projection (t2) and the fund accounting (t3, t4) share the risk charge rules: death_rate.py (probability
with medical loading and smoker factor) and death_benefit.py (sum at risk), at the age of `entry_age` and age.py.
Both Neuron generations age the insured once, at the start date (java_age.py, cobol_age.py: the generation of the
application date); the age then goes up by one every policy year (age.py, seen in the t2 offer projection).

The surrender penalty is shared by the surrender value (t3) and its check on the targets (t5). The product's scale
(NRSURR) sets a penalty rate per completed policy year; a waiver period (NRWAIV, e.g. COVID-19 from 2020-03-16 to
06-30) suspends it, and after the last year of the scale there is none.
"""
import functools
from decimal import Decimal

from neuron.calendar.policy_years import policy_years
from neuron.cobol import is_cobol
from neuron.cyymmdd import parts
from neuron.data import as_of, day, grouped, guarded, index, num, readable, table
from neuron.terms.agreements import agreed_rate
from neuron.terms.broker import broker
from neuron.terms.cobol_age import entry_age_cobol
from neuron.terms.java_age import entry_age_java

SEX_BASIS = {"M": "1", "W": "2"}  # tariff sex basis -> NRCODE SEX; "U" (unisex) uses the person's own sex


def charges(policy, legacy_date):
    """The NRCHRG row of the policy's tariff valid on the date: family (key positions 1-2) and generation (4-5).

    Admin fee CG_ADMFEE, management rates CG_AMCP1/2, smoker factor CG_SMKFAC and mortality table CG_MORTTB.
    """
    rows = index(policy.legacy_dir, "NRCHRG", "CG_TARFAM", "CG_TARGEN")[policy.tariff[:2], policy.tariff[3:5]]
    return as_of(rows, "CG", legacy_date)


def agreement(policy, fee_type, legacy_date):
    """Rate of an individual agreement (ENT or AMC) valid on the date, or None without one."""
    rows = index(policy.legacy_dir, "NRAGRE", "AG_POLNR", "AG_FEETP").get((policy.policy_id, fee_type), [])
    valid = as_of(rows, "AG", legacy_date)
    return num(valid["AG_RATE"], 6) if valid else None


def tier_rate(policy, legacy_date):
    """NRENTC entry charge of the broker's tier on the date."""
    tier = grouped(policy.legacy_dir, "NRBROK", "BR_BRKNR")[broker(policy, legacy_date)][0]["BR_TIER"]
    return num(as_of(grouped(policy.legacy_dir, "NRENTC", "EC_TIER")[tier], "EC", legacy_date)["EC_RATE"], 6)


def entry_rate(policy, legacy_date):
    """Entry charge on a premium: an ENT agreement, else the rate of the broker tier."""
    return agreed_rate(agreement(policy, "ENT", legacy_date), tier_rate, policy, legacy_date)


def management_rate(policy, pot, tariff, legacy_date):
    """Yearly management charge of a pot.

    An AMC agreement, else CG_AMCP1 for the initial units (pot 1) or CG_AMCP2 for the base units (pot 2).
    """
    return agreed_rate(agreement(policy, "AMC", legacy_date), num, tariff[f"CG_AMCP{pot}"], 6)


def allocation(policy, legacy_date):
    """{fund: share} of the allocation version valid on the date: how a premium is split over the funds (NRALLO).

    Of a set the highest version wins; the shares add up to 1. No valid set: no fund gets anything.
    """
    current = as_of(grouped(policy.legacy_dir, "NRALLO", "AL_POLNR")[policy.policy_id], "AL", legacy_date)
    versions = index(policy.legacy_dir, "NRALLO", "AL_POLNR", "AL_VRSNR")
    rows = versions[policy.policy_id, current["AL_VRSNR"]] if current else ()
    return {r["AL_FNDID"].strip(): num(r["AL_PCTG"], 6) for r in rows}


@functools.cache
def mortality(legacy_dir):
    """{(table, sex, age): yearly death probability} of NRMORT, indexed once (malformed rows left out)."""
    return dict(readable(death_probability, table(legacy_dir, "NRMORT")))


def death_probability(row):
    """((table, sex, age), probability) of one NRMORT row."""
    return (row["MO_TABID"], row["MO_SEX"], int(row["MO_AGE"])), num(row["MO_QX"], 6)


def qx(policy, tariff, age):
    """Yearly death probability at an age in the tariff's mortality table CG_MORTTB, for the insured's sex."""
    return mortality(policy.legacy_dir)[tariff["CG_MORTTB"], insured_sex(policy), age]


def insured_sex(policy):
    """Sex of the mortality table: from the tariff key (position 3), a unisex tariff (U) uses the person's own."""
    return SEX_BASIS.get(policy.tariff[2], policy.person["PS_SEX"])


@functools.cache
def entry_age(policy):
    """Age at the start date, counted like the Neuron generation of the application date."""
    count = entry_age_cobol if is_cobol(policy.first["PH_APPDT"], policy.cobol_until) else entry_age_java
    return count(parts(policy.person["PS_BIRTH"]), policy.start)


@functools.cache
def penalty_scales(legacy_dir):
    """{(scale, completed years): penalty rate} of NRSURR; the first row of a scale and year counts.

    A malformed rate is kept as None, so the policies that need it are left out instead of paying no penalty.
    """
    rates = {}
    for scale, year, rate in readable(scale_year, table(legacy_dir, "NRSURR")):
        rates.setdefault((scale, year), rate)
    return rates


def scale_year(row):
    """(scale, completed years, penalty rate or None) of one NRSURR row."""
    return row["SR_SCALE"].strip(), int(row["SR_YEAR"]), guarded(num, row["SR_RATE"], 6)


def penalty_rate(policy, legacy_date):
    """Surrender penalty of the product's scale for the completed policy years on the date."""
    if as_of(table(policy.legacy_dir, "NRWAIV"), "WV", legacy_date):
        return Decimal(0)
    scale = grouped(policy.legacy_dir, "NRPROD", "PD_PRDCD")[policy.first["PH_PRDCD"]][0]["PD_SRPSCL"]
    return penalty_scales(policy.legacy_dir).get((scale, policy_years(policy.start, day(legacy_date))), Decimal(0))
