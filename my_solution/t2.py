"""t2: projected maturity value, a replay of the offer projection (99.01 % on the train targets).

Rules found:
- parameters as valid on the application date of version 1: NRCHRG by tariff family/generation, NRENTC by the
  tier of the offer's broker, NRILLU growth rate; individual fee agreements do not apply to the offer;
- monthly loop from the start date to the month before maturity: premium net of the entry charge when due,
  then admin fee, management charge AMCP2/12, risk charge, then growth at rate/12, each step to the cent;
- risk charge = sum at risk (death benefit option A/B/C minus fund value) x qx/12 x (1 + loading) x smoker
  factor, with the age of the policy year: Java offers the nearest birthday in whole months at the
  anniversary, COBOL offers the entry age (nearest birthday from calendar days / 365) plus completed years;
- offers applied for in the COBOL era truncate every step, later offers round half up.
"""
from decimal import Decimal

from ages import risk_age
from dates import day, raw_day, rounding
from loader import by_key, number, table
from params import broker_tier, charges, entry_rate, first_version, illustration_rate

CENT = Decimal("0.01")
FREQUENCY_MONTHS = {"M": 1, "Q": 3, "H": 6, "J": 12, "E": 1200}  # E: single premium, paid in month 0 only
SEX_OF_TARIFF = {"M": "1", "W": "2"}  # position 3 of the tariff key; U takes the sex of the insured person


def offer(legacy_dir, policy, risk, person):
    """Parameters of the projection as of the application date of version 1.

    Amounts are Decimal in policy currency, `birth` is the raw (y, m, d) of the insured person.
    """
    head = first_version(legacy_dir, policy)
    applied, key, mode = day(head["PH_APPDT"]), risk["RK_TARKEY"], rounding(day(head["PH_APPDT"]))
    charge = charges(legacy_dir, key[:2], key[3:5], applied)
    smoker = number(charge["CG_SMKFAC"], 6) if person["PS_SMOKE"] in ("J", "Y") else Decimal(1)
    entry = entry_rate(legacy_dir, broker_tier(legacy_dir, head["PH_BRKNR"]), applied)
    return dict(
        applied=applied, begin=day(head["PH_BEGDT"]), end=day(head["PH_ENDDT"]), step=FREQUENCY_MONTHS[head["PH_FREQ"]],
        rounding=mode, net_premium=(number(head["PH_PREMI"], 2) * (1 - entry)).quantize(CENT, mode),
        admin=number(charge["CG_ADMFEE"], 2), amc=number(charge["CG_AMCP2"], 6), table=charge["CG_MORTTB"],
        growth=1 + illustration_rate(legacy_dir, applied) / 12, option=key[6],
        sum_insured=number(risk["RK_SUMIN"], 2), risk_factor=(1 + number(risk["RK_LOAD"], 6)) * smoker,
        sex=person["PS_SEX"] if key[2] == "U" else SEX_OF_TARIFF[key[2]], birth=raw_day(person["PS_BIRTH"]))


def risk_charge(q, qx, value, month):
    """Monthly risk charge on the sum at risk of the death benefit option.

    A: 101 % of the fund value, B: the higher of sum insured and fund value, C: fund value plus sum insured.
    The age is the one of the policy year (ages.risk_age: COBOL offers entry age + years, Java whole months).
    """
    benefit = {"A": value * Decimal("1.01"), "B": max(q["sum_insured"], value), "C": value + q["sum_insured"]}
    at_risk = max(benefit[q["option"]] - value, Decimal(0))
    age = risk_age(q["applied"], q["begin"], q["birth"], month // 12)
    return at_risk * qx[(q["table"], q["sex"], age)] / 12 * q["risk_factor"]


def project(q, qx):
    """Fund value at maturity after the monthly loop.

    Order within a month: premium, admin fee, management charge, risk charge, growth; each result to the cent.
    """
    months = (q["end"].year - q["begin"].year) * 12 + q["end"].month - q["begin"].month
    value = Decimal(0)
    for month in range(months):
        if month % q["step"] == 0:  # premium due: every `step` months, a single premium once
            value += q["net_premium"]
        value -= q["admin"]  # the admin fee is a fixed cent amount, nothing to round
        value -= (value * q["amc"] / 12).quantize(CENT, q["rounding"])
        value -= risk_charge(q, qx, value, month).quantize(CENT, q["rounding"])
        value = (value * q["growth"]).quantize(CENT, q["rounding"])
    return value


def solve(legacy_dir):
    """{policy_id: maturity_value}

    A policy outside the parameter tables (e.g. an age beyond the mortality table) is left out, not fatal.
    """
    persons = by_key(legacy_dir, "NRPERS", "PS_PERNR")
    qx = {(m["MO_TABID"], m["MO_SEX"], int(m["MO_AGE"])): number(m["MO_QX"], 6) for m in table(legacy_dir, "NRMORT")}
    out = {}
    for policy, risk in by_key(legacy_dir, "NRRISK", "RK_POLNR").items():
        try:
            out[policy] = project(offer(legacy_dir, policy, risk, persons[risk["RK_PERNR"]]), qx)
        except LookupError:
            continue
    return out
