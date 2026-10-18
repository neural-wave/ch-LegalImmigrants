"""t2 projected maturity value: the value at maturity that the signed offer projected (neuron/offer/ has its steps).

Offers signed before the COBOL -> Java conversion truncate the cents and count ages in 365-day years.
The year-end values of the projection are the diagnostic file t2_projection_year.csv.

The offer projection: Neuron's simplified month-by-month accounting of a policy, as printed on the signed offer.

The whole value is one amount, without fund prices, currencies or individual agreements. Every month, in this order:
premium net of the entry charge in, admin fee out, management charge out, risk charge out, then growth by a twelfth
of the yearly NRILLU rate. Each step is rounded to the cent: half up in Java Neuron, truncated in COBOL Neuron.
The offer was calculated when the customer signed it, so every parameter is the one valid on the application date
PH_APPDT, and the policy data is its first version.
"""
from decimal import Decimal
from itertools import accumulate

from neuron.calendar.month_count import months_between
from neuron.cobol import is_cobol
from neuron.contract import cents, contract
from neuron.data import FREQ_MONTHS, MONTHS, as_of, day, grouped, guarded, num, table
from neuron.offer.fee_step import after_fees
from neuron.offer.growth_step import grown
from neuron.offer.offer_age import offer_age
from neuron.offer.premium_step import with_premium
from neuron.offer.risk_step import after_risk
from neuron.terms.death_rate import death_rate
from neuron.terms.net_premium import net_premium
from neuron.terms.rates import charges, tier_rate


class Offer:
    """The projection of one policy (a Contract) with the parameters of its application date."""

    def __init__(self, policy):
        offered, signed = policy.first, policy.first["PH_APPDT"]
        self.policy, self.tariff, self.cobol = policy, charges(policy, signed), is_cobol(signed, policy.cobol_until)
        self.months = months_between(policy.start, day(offered["PH_ENDDT"]))
        self.step = FREQ_MONTHS.get(offered["PH_FREQ"], self.months)  # a single premium (E) is paid once
        self.premium = cents(net_premium(num(offered["PH_PREMI"], 2), tier_rate(policy, signed)), self.cobol)
        self.admin, self.management = num(self.tariff["CG_ADMFEE"], 2), num(self.tariff["CG_AMCP2"], 6)
        self.growth = num(as_of(table(policy.legacy_dir, "NRILLU"), "IL", signed)["IL_RATE"], 6)

    def month(self, value, month):
        """The value after one month: premium in, admin and management charges out, risk charge out, then growth."""
        value = with_premium(value, self.premium, month, self.step)
        value = after_fees(value, self.admin, self.management, self.cobol)
        death = death_rate(self.policy, self.tariff, offer_age(self.policy, month))
        return grown(after_risk(self.policy, value, death, self.cobol), self.growth, self.cobol)

    def year_ends(self):
        """The projected value at the end of every policy year; the last one is the maturity value."""
        return list(accumulate(range(self.months), self.month, initial=Decimal(0)))[MONTHS::MONTHS]


def maturity_value(legacy_dir, policy_id):
    """(policy_id, the last year-end value of the policy's offer projection)."""
    *_, maturity = Offer(contract(legacy_dir, policy_id)).year_ends()
    return policy_id, maturity


def t2_projected_maturity_value(legacy_dir) -> dict[str, Decimal]:
    """{policy_id: maturity_value} of every policy; policies with incomplete data are left out."""
    policies = grouped(legacy_dir, "NRPOLH", "PH_POLNR")
    return dict(filter(None, (guarded(maturity_value, legacy_dir, policy_id) for policy_id in policies)))
