"""A policy's contract data for the fund accounting: versions, insured risk, events, premiums and rounding era.

The rates that apply to a policy on a date are in neuron/terms/ (rates, agreements, death rate, ages).
Values that never change for a policy (start date, currency, tariff key) are read once.

The two Neuron generations: COBOL Neuron until the conversion to Java (event 800), Java Neuron after it. The
conversion is the one real boundary in the rules (cobol.py tells the era of a date). COBOL Neuron truncated amounts
and units where Java rounds half up; it also counted ages in 365-day years and accrued management charges on a
360-day year.
"""
import functools
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal

from neuron.cobol import is_cobol
from neuron.data import day, grouped, guarded, index, num
from neuron.market import market
from neuron.reversals import skipped_events

CONVERSION_EVENT = "800"  # NRCODE EVTTP
CENT = Decimal("0.01")
UNIT = Decimal("0.000001")
MAIN_RISK = "1"  # RK_RSKNR of the insured risk the charges are for; others would be riders


@functools.cache
def conversion_date(legacy_dir):
    """Legacy date of the COBOL -> Java conversion (2007-08-11 in the train export); unreadable dates are ignored."""
    conversions = grouped(legacy_dir, "NREVNT", "EV_EVTTP")[CONVERSION_EVENT]
    return min(filter(None, (guarded(int, event["EV_EFFDT"]) for event in conversions)))


def rounding(cobol):
    """Java Neuron rounds half up; COBOL Neuron truncated, so its policies lost a cent now and then."""
    return ROUND_DOWN if cobol else ROUND_HALF_UP


def rounded(amount, unit, cobol=False):
    """`amount` rounded to `unit` (0.01 for money, 0.000001 for fund units) like the Neuron generation that made it."""
    return amount.quantize(unit, rounding=rounding(cobol))


def rounder(unit, cobol):
    """`rounded` as a function of the amount alone, for the many amounts of one charge run."""
    return functools.partial(Decimal.quantize, exp=unit, rounding=rounding(cobol))


def cents(amount, cobol=False):
    """Money rounded to the cent, half up unless COBOL Neuron calculated it (see `rounded`)."""
    return rounded(amount, CENT, cobol)


class Contract:
    """One policy: its versions, main insured risk and person, events and premiums.

    `cents` and `units` round like the Neuron generation of a date: COBOL truncates, Java rounds half up.
    """

    def __init__(self, legacy_dir, policy_id):
        self.legacy_dir, self.policy_id = legacy_dir, policy_id
        self.market = market(legacy_dir)
        self.cobol_until = conversion_date(legacy_dir)
        self.versions = grouped(legacy_dir, "NRPOLH", "PH_POLNR")[policy_id]
        self.risk = index(legacy_dir, "NRRISK", "RK_POLNR", "RK_RSKNR")[policy_id, MAIN_RISK][0]
        self.person = grouped(legacy_dir, "NRPERS", "PS_PERNR")[self.risk["RK_PERNR"].strip()][0]
        # currency, product and start date never change between versions
        self.first = min(self.versions, key=lambda v: int(v["PH_VRSNR"]))
        self.currency, self.start = self.first["PH_CCY"], day(self.first["PH_BEGDT"])
        # tariff key, e.g. FXU03LC: family, sex basis, generation, premium type, death benefit option
        self.tariff = self.risk["RK_TARKEY"].strip()
        self.sum_insured = num(self.risk["RK_SUMIN"], 2)

    @functools.cached_property
    def events(self):
        """{event number: NREVNT row} of the policy."""
        return {int(e["EV_EVTNR"]): e for e in grouped(self.legacy_dir, "NREVNT", "EV_POLNR")[self.policy_id]}

    def event_date(self, event):
        """The effective date of one of the policy's events."""
        return day(self.events[event]["EV_EFFDT"])

    @functools.cached_property
    def skipped(self):
        """Events whose bookings don't count (reversals.py)."""
        return skipped_events(self.events)

    @functools.cached_property
    def premiums(self):
        """{booking event: amount received} of the premium items (NRPREM.PR_EVTNR links them)."""
        items = grouped(self.legacy_dir, "NRPREM", "PR_POLNR")[self.policy_id]
        return {int(p["PR_EVTNR"]): num(p["PR_AMTRC"], 2) for p in items}

    def cents(self, amount, legacy_date):
        """An amount rounded to the cent like the Neuron generation of that date."""
        return cents(amount, is_cobol(legacy_date, self.cobol_until))

    def units(self, amount, legacy_date):
        """Units rounded to 6 decimals like the Neuron generation of that date."""
        return rounded(amount, UNIT, is_cobol(legacy_date, self.cobol_until))

    def rounders(self, legacy_date):
        """(cents, units): `cents` and `units` of one date as functions of the amount alone, for a charge run."""
        cobol = is_cobol(legacy_date, self.cobol_until)
        return rounder(CENT, cobol), rounder(UNIT, cobol)


contract = functools.cache(Contract)  # one Contract per policy and export, shared by t2 to t5
