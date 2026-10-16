"""t4: annual statement per calendar year (97 % on the train targets).

Rules found (opening briefing and train targets):
- a statement exists for every year from the start year to the year the policy ends (first version in state
  60 surrender or 70 death), at the latest 2025;
- premiums = premium items in state P by the year of the money received date (NRPREM);
- entry charges = premium x allocation share - invested amount of every PRM booking, by the year of the
  booking's own trade date (the fund bookings of one premium can straddle a year end);
- admin, management and risk charges = the amounts of the ADM / AMC / RSK bookings by trade-date year;
- total = entry + admin + management + risk (premiums are not a charge).
"""
import collections
import functools
from decimal import ROUND_HALF_UP, Decimal

from accounting import ledger
from dates import day
from loader import grouped, number, table
from market import CENT
from params import first_version, policy_versions

ZERO = Decimal(0)
LAST_YEAR = 2025
COLUMNS = ("PRM", "ADM", "AMC", "RSK")  # entry charges are kept under the PRM bookings they belong to


def statement_years(legacy_dir, policy):
    """range of the statement years: start year .. year of the first version in state 60/70, capped at 2025."""
    begin = day(first_version(legacy_dir, policy)["PH_BEGDT"]).year
    ended = [day(v["PH_VLDFR"]).year for v in policy_versions(legacy_dir, policy) if v["PH_STATE"] in ("60", "70")]
    return range(begin, min(ended[0] if ended else LAST_YEAR, LAST_YEAR) + 1)


@functools.lru_cache(maxsize=None)
def premiums(legacy_dir):
    """{(policy, year): premiums received}, items in state P by the year of PR_RCVDT."""
    out = collections.defaultdict(Decimal)
    for r in table(legacy_dir, "NRPREM"):
        if r["PR_STATE"] == "P" and (received := day(r["PR_RCVDT"])):
            out[(r["PR_POLNR"], received.year)] += number(r["PR_AMTRC"], 2)
    return out


def statement(legacy_dir, policy, year):
    """(premiums, entry_charges, admin_fees, management_fees, risk_charges, total_charges) of one year."""
    amounts = ledger(legacy_dir).yearly.get((policy, year), {})
    values = [premiums(legacy_dir).get((policy, year), ZERO)] + [amounts.get(c, ZERO) for c in COLUMNS]
    values = [v.quantize(CENT, ROUND_HALF_UP) for v in values]  # entry charges carry fractions of a cent
    return tuple(values + [sum(values[1:], ZERO)])


def solve(legacy_dir):
    """{(policy_id, year): statement} for every policy of NRPOLH."""
    return {(policy, year): statement(legacy_dir, policy, year)
            for policy in grouped(legacy_dir, "NRPOLH", "PH_POLNR") for year in statement_years(legacy_dir, policy)}
