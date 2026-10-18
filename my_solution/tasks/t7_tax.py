"""t7 tax audit: the taxes Neuron withheld from every payout and remitted, and the tax amounts per policy and year.

Which taxes Neuron booked is in NRTAXB; their amounts come from the rules in neuron/tax_bookings.py. A payout row
shows the residence Neuron used, the base of the withholding tax, the tax, its surcharges, the stamp duty collected
and the day the taxes were due at the tax office. Checked against the leaderboard samples Lifeware released.
"""
import datetime as dt
from decimal import Decimal

from neuron.calendar.easter import easter
from neuron.calendar.month_shift import month_shift
from neuron.data import day, guarded
from neuron.tax_bookings import ledgers

WITHHOLDING, SURCHARGES, STAMP_DUTY = ("VST", "SOS", "KST"), ("SOL", "KIS"), ("BOC",)
STAMP_DUTIES = ("STP", "BOL")  # annual columns booked on their own dates; the withheld taxes count when remitted
ANNUAL = ("STP", "VST", "SOS", "BOL", "KST", "SOL", "KIS")  # ch_stp, ch_vst, it_sos, it_bol, de_kst, de_sol, de_kis
ZERO = Decimal("0.00")

# The deadline of the country of the tax: ("day", n) the n-th of the next month (DE 10th, IT 16th), ("after_month",
# n) n days after the end of the payout's month (CH 30); a deadline on a weekend or public holiday of that country
# moves to its next business day (samples: IT 2017-04-16 → 04-18, DE 2004-10-10 → 10-11, CH 2017-12-30 → 2018-01-03)
DEADLINES = {"DE": ("day", 10), "IT": ("day", 16), "CH": ("after_month", 30)}
# National public holidays: fixed (month, day) and days counted from Easter Sunday
HOLIDAYS = {
    "CH": (((1, 1), (1, 2), (8, 1), (12, 25), (12, 26)), (-2, 1, 39, 50)),
    "DE": (((1, 1), (5, 1), (10, 3), (12, 25), (12, 26)), (-2, 1, 39, 50)),
    "IT": (((1, 1), (1, 6), (4, 25), (5, 1), (6, 2), (8, 15), (11, 1), (12, 8), (12, 25), (12, 26)), (1,)),
}
# taxable_base of a payout without withholding tax (samples): CH the payout (Neuron tests it against the VST
# threshold), every other country 0.00
UNTAXED_BASE_PAYOUT = ("CH",)


def holidays(country, year):
    """The public holidays of a country in a year."""
    fixed, from_easter = HOLIDAYS[country]
    return {*(dt.date(year, m, d) for m, d in fixed), *(easter(year) + dt.timedelta(days=n) for n in from_easter)}


def business_day(country, d):
    """The day itself, or the next day that is no weekend and no public holiday of the country."""
    while d.weekday() >= 5 or d in holidays(country, d.year):
        d += dt.timedelta(days=1)
    return d


def remittance_date(country, legacy_date):
    """The day the taxes of a payout on a date were due at the tax office of the country (DEADLINES)."""
    kind, n = DEADLINES[country]
    paid_on = day(legacy_date)
    if kind == "day":
        return business_day(country, dt.date(*month_shift(paid_on, 1), n))
    month_end = dt.date(*month_shift(paid_on, 1), 1) - dt.timedelta(days=1)
    return business_day(country, month_end + dt.timedelta(days=n))


def total(ledger, event, kinds):
    """The amount of some tax types booked for one payout; 0.00 when none of them was booked."""
    return sum((ledger.amounts.get((event, kind), ZERO) for kind in kinds), ZERO)


def due(ledger, payout):
    """The remittance date of a payout, None when nothing was withheld (stamp duty alone doesn't count, Lifeware)."""
    withheld = total(ledger, payout.event, WITHHOLDING + SURCHARGES)
    return remittance_date(ledger.countries[payout.event], payout.date) if withheld else None


def payout_row(ledger, payout):
    """(country, taxable_base, withholding, surcharges, stamp_duty, remittance_date) of one payout."""
    amounts = [total(ledger, payout.event, kinds) for kinds in (WITHHOLDING, SURCHARGES, STAMP_DUTY)]
    untaxed = payout.amount if payout.country in UNTAXED_BASE_PAYOUT else ZERO
    return (payout.country, ledger.bases.get(payout.event, untaxed), *amounts, due(ledger, payout))


def t7_tax_payout(legacy_dir) -> dict[tuple[str, int], tuple]:
    """{(policy_id, event_nr): (country, taxable_base, withholding, surcharges, stamp_duty, remittance_date)}

    Every counted payout (withdrawal, surrender, death claim), taxed or not.
    """
    rows = {(policy_id, event): guarded(payout_row, ledger, payout)
            for policy_id, ledger in ledgers(legacy_dir).items() for event, payout in ledger.payouts.items()}
    return {key: row for key, row in rows.items() if row}


def annual_amounts(ledger):
    """[(year, tax type, amount)]: the stamp duties in the year of their effective date, the taxes withheld from a
    payout in the year they were remitted (samples: a December payout counts in the next year)."""
    amounts = [(year, kind, amount) for year, kind, amount in ledger.annual if kind in STAMP_DUTIES]
    for event, payout in ledger.payouts.items():
        if remitted := due(ledger, payout):
            amounts += [(remitted.year, kind, ledger.amounts.get((event, kind), ZERO))
                        for kind in WITHHOLDING + SURCHARGES]
    return amounts


def annual_rows(policy_id, ledger):
    """{(policy_id, year): amounts per ANNUAL column} of the years with an amount."""
    years = {}
    for year, kind, amount in annual_amounts(ledger):
        if amount:
            years.setdefault((policy_id, year), dict.fromkeys(ANNUAL, ZERO))[kind] += amount
    return {key: tuple(columns.values()) for key, columns in years.items()}


def t7_tax_annual(legacy_dir) -> dict[tuple[str, int], tuple[Decimal, ...]]:
    """{(policy_id, year): (ch_stp, ch_vst, it_sos, it_bol, de_kst, de_sol, de_kis)}

    Only years with at least one amount; BOC is not a column (it collects BOL already counted).
    """
    rows = {}
    for policy_id, ledger in ledgers(legacy_dir).items():
        rows.update(guarded(annual_rows, policy_id, ledger) or {})
    return rows
