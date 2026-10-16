"""Parameters and formulas of one monthly charge run: tariff charges, AMC and risk formulas, mortality rate.

Rules found:
- admin fee, AMC rates, smoker factor and mortality table come from the NRCHRG row of the tariff family
  (key positions 1-2) and generation (positions 4-5) valid on the trade date;
- an agreed AMC rate (NRAGRE) valid on the trade date replaces the rates of both pots;
- AMC: pot 1 at CG_AMCP1, pot 2 at CG_AMCP2; Java: value x rate / 12 rounded half up; COBOL pro rata
  temporis: value x rate x days / 360 truncated, days since the previous run; the first run counts from the
  monthly anniversary before it, even when the policy started earlier (first premium paid late);
- RSK: sum at risk x qx / 12 x (1 + loading) x smoker factor; sum at risk by death benefit option: A 1 % of
  the value, B sum insured minus value (at least 0), C the sum insured;
- risk: sum insured, death benefit option (key position 7) and medical loading from NRRISK, the smoker
  factor of the tariff for smokers (PS_SMOKE = J), sex from key position 3 (M/W), U = the insured's sex;
- age at the last policy anniversary on or before the trade date, by the era of the APPLICATION date for the
  whole life of the policy (ages.risk_age): COBOL offers entry age (nearest birthday from calendar days /
  365, impossible birth days clipped to the month end) + completed policy years, Java offers the nearest
  birthday in whole months.
"""
import collections
import functools
from decimal import Decimal

from ages import risk_age
from dates import add_months, day, is_legacy, raw_day
from loader import by_key, number, table
from market import CENT, rounded
from params import agreed_rate, charges, first_version

ZERO = Decimal(0)
SEX_OF_TARIFF = {"M": "1", "W": "2"}
# parameters of one run: policy currency, days since the previous run, admin fee, AMC rates of pot 1 / pot 2,
# agreed AMC rate (or None), death benefit option, sum insured, (1 + loading) x smoker factor, qx
Run = collections.namedtuple("Run", "currency days admin amc1 amc2 agreed option sum_insured factor qx")
tariff_charges = functools.lru_cache(maxsize=None)(charges)  # the same (family, generation, date) recurs


@functools.lru_cache(maxsize=None)
def mortality(legacy_dir):
    """{(table, sex, age): qx} (NRMORT)."""
    return {(m["MO_TABID"], m["MO_SEX"], int(m["MO_AGE"])): number(m["MO_QX"], 6) for m in table(legacy_dir, "NRMORT")}


def policy_year(begin, traded):
    """Completed policy years at the last anniversary on or before `traded` (0 in the first year)."""
    # the anniversary of a 29 February start falls on 28 February in common years, like the charge run
    years = traded.year - begin.year
    return years - (traded < add_months(begin, 12 * years, begin.day))


def parameters(legacy_dir, policy, traded, previous):
    """Run parameters of the charge run of `policy` on `traded`; `previous` is the date of the run before."""
    head, risk = first_version(legacy_dir, policy), by_key(legacy_dir, "NRRISK", "RK_POLNR")[policy]
    person, key = by_key(legacy_dir, "NRPERS", "PS_PERNR")[risk["RK_PERNR"]], risk["RK_TARKEY"]
    begin = day(head["PH_BEGDT"])
    # NRCHRG row of family / generation valid on the trade date
    charge = tariff_charges(legacy_dir, key[:2], key[3:5], traded)
    # smoker factor for smokers, sex basis M/W of the tariff, else the insured person's sex
    smoker = number(charge["CG_SMKFAC"], 6) if person["PS_SMOKE"] == "J" else Decimal(1)
    sex = SEX_OF_TARIFF.get(key[2], person["PS_SEX"])
    # age of the policy year: COBOL offers (application date) entry age + years, Java offers whole months
    age = risk_age(day(head["PH_APPDT"]), begin, raw_day(person["PS_BIRTH"]), policy_year(begin, traded))
    # an age outside the mortality table means no risk charge
    qx = mortality(legacy_dir).get((charge["CG_MORTTB"], sex, age), ZERO)
    # the first run counts its days from the anniversary one month back (on the start's day of month)
    since = previous or add_months(traded, -1, begin.day)
    return Run(head["PH_CCY"], (traded - since).days, number(charge["CG_ADMFEE"], 2),
               number(charge["CG_AMCP1"], 6), number(charge["CG_AMCP2"], 6),
               agreed_rate(legacy_dir, policy, "AMC", traded), key[6], number(risk["RK_SUMIN"], 2),
               (1 + number(risk["RK_LOAD"], 6)) * smoker, qx)


def management_fee(value, rate, days, date):
    """AMC of one pot: COBOL pro rata temporis on 360 days (truncated), Java one twelfth (half up)."""
    return rounded(value * rate * days / 360 if is_legacy(date) else value * rate / 12, CENT, date)


def risk_charge(value, run, date):
    """Monthly risk charge on the sum at risk of the death benefit option (A 1 %, B shortfall, C sum insured)."""
    at_risk = {"A": value / 100, "B": max(run.sum_insured - value, ZERO), "C": run.sum_insured}[run.option]
    # divide last: 6875 x 0.00368 / 12 x 3 is 6.32499... in 28-digit Decimal, but the system got 6.325 -> 6.33
    return rounded(at_risk * run.qx * run.factor / 12, CENT, date)
