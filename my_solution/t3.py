"""t3: surrender value of every policy on the valuation dates (96 % on the train targets).

Rules found:
- policy value = sum over fund/pots of units x last bid price on or before the valuation date / fx ratio of
  that date, each fund/pot rounded to the cent by the era of the VALUATION date (2006-12-31 truncates);
- surrender value = policy value minus the penalty of the product's surrender scale (NRSURR) for the completed
  policy years since the start date, the penalty rounded half up; no penalty in a NRWAIV period;
- a policy surrendered (state 60) or ended by death (state 70) on the valuation date has value 0.
"""
import functools
from decimal import ROUND_HALF_UP, Decimal

from accounting import ledger
from dates import day
from loader import by_key, grouped, number, table
from market import CENT, fx_ratio, price, rounded
from params import first_version, policy_version, valid_on

ZERO = Decimal(0)


def policy_value(legacy_dir, policy, date):
    """Value of the holdings on `date` in policy currency, every fund/pot to the cent."""
    currency, total = first_version(legacy_dir, policy)["PH_CCY"], ZERO
    for (fund, _), units in ledger(legacy_dir).holdings(policy, date).items():
        bid, fx = price(legacy_dir, fund, date), fx_ratio(legacy_dir, currency, fund, date)
        if units and bid and fx:  # a fund without a price yet adds nothing
            total += rounded(units * bid / fx, CENT, date)
    return total


@functools.lru_cache(maxsize=None)
def scales(legacy_dir):
    """{(scale, completed years): penalty rate} (NRSURR); no row means no penalty."""
    return {(int(r["SR_SCALE"]), int(r["SR_YEAR"])): number(r["SR_RATE"], 6) for r in table(legacy_dir, "NRSURR")}


def penalty_rate(legacy_dir, policy, date):
    """Surrender penalty rate on `date`: by completed policy years from the start date, 0 in a waiver period."""
    if valid_on(table(legacy_dir, "NRWAIV"), "WV_", date):
        return ZERO
    head = first_version(legacy_dir, policy)
    begin = day(head["PH_BEGDT"])
    years = date.year - begin.year - ((date.month, date.day) < (begin.month, begin.day))
    scale = int(by_key(legacy_dir, "NRPROD", "PD_PRDCD")[head["PH_PRDCD"]]["PD_SRPSCL"])
    return scales(legacy_dir).get((scale, years), ZERO)


def surrender_value(legacy_dir, policy, date):
    """Policy value minus the penalty; 0 once the policy is surrendered or the insured has died."""
    version = policy_version(legacy_dir, policy, date)
    if version is not None and version["PH_STATE"] in ("60", "70"):
        return ZERO
    value = policy_value(legacy_dir, policy, date)
    return value - (value * penalty_rate(legacy_dir, policy, date)).quantize(CENT, ROUND_HALF_UP)


def solve(legacy_dir, valuation_dates):
    """{(policy_id, valuation_date): surrender_value} for every policy of NRPOLH."""
    return {(policy, date): surrender_value(legacy_dir, policy, date)
            for policy in grouped(legacy_dir, "NRPOLH", "PH_POLNR") for date in valuation_dates}
