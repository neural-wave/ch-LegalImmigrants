"""Investment of a premium: the blank amount and units of the PRM bookings in NRBOOK.

Rules found:
- the items of one booking event are added up: the premium of the event is the sum of their PR_AMTRC;
- invested amount = premium x (1 - entry rate) x allocation share of the fund, rounded to the cent;
- the entry rate is the individually agreed ENT rate (NRAGRE), else the NRENTC rate of the broker's tier;
  the broker is the one of the policy version valid on the money date (version 1 in a gap);
- the allocation share is the highest NRALLO version of the fund valid on the money date;
- units = amount x fx / ask price to 6 decimals; ask price of the price date, exchange rates of the day
  BEFORE the trade date; every rounding follows the era of the trade date;
- the entry charge of the booking (t4) is premium x share minus the invested amount.
"""
import collections
import datetime as dt
import functools
from decimal import Decimal

from loader import grouped, number, table
from market import CENT, UNIT, fx_ratio, price, rounded
from params import agreed_rate, broker_tier, entry_rate, first_version, policy_version, valid_on

ONE_DAY = dt.timedelta(days=1)


@functools.lru_cache(maxsize=None)
def received(legacy_dir):
    """{(policy, event): amount received}, the premium items of one booking event added up (NRPREM)."""
    out = collections.defaultdict(Decimal)
    for r in table(legacy_dir, "NRPREM"):
        out[(r["PR_POLNR"], r["PR_EVTNR"])] += number(r["PR_AMTRC"], 2)
    return out


def allocation_share(legacy_dir, policy, fund, date):
    """Share of the premium going to `fund` as of `date`: the highest allocation version of that fund (NRALLO)."""
    rows = [r for r in grouped(legacy_dir, "NRALLO", "AL_POLNR").get(policy, []) if r["AL_FNDID"] == fund]
    rows = valid_on(rows, "AL_", date)
    # several allocation sets can be valid at once: the highest version number wins
    return number(max(rows, key=lambda r: int(r["AL_VRSNR"]))["AL_PCTG"], 6) if rows else None


def entry_charge_rate(legacy_dir, policy, date):
    """Entry rate as of the money date: the agreed ENT rate, else the tariff rate of the broker's tier."""
    rate = agreed_rate(legacy_dir, policy, "ENT", date)
    if rate is None:
        # money received in a gap between two versions: the original broker of version 1 applies
        head = policy_version(legacy_dir, policy, date) or first_version(legacy_dir, policy)
        rate = entry_rate(legacy_dir, broker_tier(legacy_dir, head["PH_BRKNR"]), date)
    return rate


def invest(legacy_dir, policy, event, fund, money_date, traded, priced):
    """(invested amount, units, entry charge) of one PRM booking; (None, None, None) if a parameter is missing."""
    premium = received(legacy_dir).get((policy, event))
    share = allocation_share(legacy_dir, policy, fund, money_date)
    # ask price of the price date; fx of the day before the trade date (the order was priced overnight)
    ask = price(legacy_dir, fund, priced, ask=True)
    fx = fx_ratio(legacy_dir, first_version(legacy_dir, policy)["PH_CCY"], fund, traded - ONE_DAY)
    if premium is None or share is None or not ask or not fx:
        return None, None, None
    # net premium of the fund to the cent, then units to 6 decimals, both in the era of the trade date
    amount = rounded(premium * (1 - entry_charge_rate(legacy_dir, policy, money_date)) * share, CENT, traded)
    units = rounded(amount * fx / ask, UNIT, traded)
    return amount, units, premium * share - amount
