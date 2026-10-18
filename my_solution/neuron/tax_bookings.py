"""The amounts of Neuron's tax bookings (NRTAXB): the export says which taxes were booked, not how much.

Every amount is the rate of NRTAXR known at the booking (taxes.py) times a base in the tax currency, rounded to the
cent in the era of the booking. Bookings of one run are processed in Neuron's order: by timestamp, the stamp duty
accrued first, then the taxes, their surcharges and the stamp duty collected (ORDER).

    STP  Swiss stamp duty on a single premium, in francs on the day it was received
    VST  Swiss withholding tax on the whole payout (booked for tax status E above TX_THRSH)
    SOS  Italian substitute tax on the gain
    KST  German capital gains tax on the gain, less the partial exemption (TFS) and halved by the half-income rule
    SOL  German solidarity surcharge on the KST
    KIS  German church tax on the KST, at the rate of the holder's region
    BOL  Italian stamp duty on the policy value at every year end, and pro rata of the year at a final payout; a
         BOL booking on any other day (TAXFIX19) restates the earlier ones at the rates known then
    BOC  the stamp duty collected at a payout: its share (EV_PCTG) of the BOL not collected yet

Evidence: both PDF examples (KST/SOL of BL10000086 #121, BOL 2019 of BL10000044 with its restatement) and the
presence of every booking type in NRTAXB; the alternatives we tested fit worse.
"""
import datetime as dt
import functools
import pathlib
from decimal import Decimal

from neuron.contract import cents, contract
from neuron.cyymmdd import parts
from neuron.data import day, grouped, guarded, num
from neuron.funds.replay import accounts
from neuron.legacy import legacy
from neuron.taxes import (PAYOUT_EVENTS, exchange, known, payouts, premium_items, readable_rates, residence, tax_cents,
                          tax_currency, tax_rate)
from neuron.valuation import pot_value

CALCULATE = {"STP": "premium_stamp", "VST": "payout_tax", "SOS": "gain_tax", "KST": "capital_gains_tax",
             "SOL": "surcharge", "KIS": "surcharge", "BOL": "stamp_duty", "BOC": "collect"}  # NRCODE TAXTP
ORDER = {"BOL": 0, "SOL": 2, "KIS": 2, "BOC": 3}  # within one run; the taxes themselves are 1
OWN_EVENT = ("STP", "BOL")  # STP books on its premium event, BOL on event 0; the other taxes on a payout event
SURCHARGED = "KST"  # SOL and KIS are a share of it
COLLECTS = {"BOC": "BOL"}  # BOC has no rate of its own: it collects the BOL accrued
YEAR_END = (12, 31)  # BOL is due on the policy value at every year end
YEAR_DAYS = 365  # the year of BOL_FINAL_DAYS "since_start"
# Choices the data can't settle (kept as named switches below): BOL of a policy's first year on the full value
# ("full") or pro rata of its days from the start ("prorated"); German church tax added on top of the KST ("on_top")
# or deductible, which lowers the KST to rate / (1 + rate x church rate) ("deductible", German law)
BOL_FIRST_YEAR = "full"
# BOL at a final payout: its days are the day of the year over 365 or 366 ("day_of_year"), or the days since
# max(1 January, policy start) over 365 ("since_start")
BOL_FINAL_DAYS = "day_of_year"
# The stamp duty a payout collects: the BOL booked before it ("booked", by TB_CHGTS), or every BOL with an effective
# date up to the payout's ("effective", also the year-end BOL the 10 January run books after a payout in early January)
BOC_COLLECTS = "booked"
# STP on a single premium (no PDF example, no Lifeware answer): the FX date of a non-CHF premium ("received": PR_RCVDT
# = TB_EFFDT, "due": PR_DUEDT, "traded": the first trade date of its PRM bookings), the amount ("received": PR_AMTRC,
# "due": PR_AMTDU) and the rounding ("converted": the CHF premium rounded, then the tax; "once": only the tax)
STP_FX_DATE, STP_AMOUNT, STP_ROUNDING = "received", "received", "converted"
STP_COLUMNS = {"received": ("PR_RCVDT", "PR_AMTRC"), "due": ("PR_DUEDT", "PR_AMTDU")}
# German taxes as in the samples: no partial exemption (2020 and 2024 rows = full gain), surcharges cut to the cent
# (BL10001204: 28.71 x 5.5 % = 1.579 → 1.57)
PARTIAL_EXEMPTION = False
CHURCH_TAX = "deductible"  # samples: BL10001204 KST 117.44 x 25 % / 1.0225 = 28.71
# Half-income rule from German law, not from the data (a guess): policies started from 2005, held 12 years, paid out
# at 60 or later (62 for policies started from 2012)
HEV_FROM, HEV_YEARS, HEV_AGES = 1050101, 12, ((1120101, 62), (0, 60))


def age_on(birth, legacy_date):
    """Completed years from a legacy date to another (also for the few impossible birth dates).

    One more on every anniversary: the holder's age and the years a policy was held.
    """
    (y0, m0, d0), (y1, m1, d1) = parts(birth), parts(legacy_date)
    return y1 - y0 - ((m1, d1) < (m0, d0))


def booking_order(row):
    """Neuron's order of the bookings: processing timestamp, ORDER within one run, then booking id.

    So a surcharge sees its tax and a collection sees the stamp duty accrued the same day.
    """
    first = int(row["TB_EFFDT"]) if BOC_COLLECTS == "effective" else int(row["TB_CHGTS"])
    return first, ORDER.get(row["TB_TAXTP"], 1), int(row["TB_CHGTS"]), int(row["TB_BOOKID"])


class Ledger:
    """The tax bookings of one policy with their amounts.

    amounts: {(event, tax type): amount}, bases: {event: base of its withholding tax}, countries: {event: country
    of its first tax}, annual: [(year, tax type, amount)] of every booking. accrued: {date: [base, amount]} of the
    stamp duty, kept for restatements; stamp_duties and collected: the BOL booked and the BOC collected so far.
    """

    def __init__(self, legacy_dir, policy_id, replayed):
        self.legacy_dir, self.policy, self.replayed = legacy_dir, contract(legacy_dir, policy_id), replayed
        self.payouts = {p.event: p for p in payouts(self.policy)}
        self.amounts, self.bases, self.countries, self.annual, self.accrued = {}, {}, {}, [], {}
        self.stamp_duties = self.collected = Decimal(0)
        rows = sorted(grouped(legacy_dir, "NRTAXB", "TB_POLNR").get(policy_id, []), key=booking_order)
        self.booked = {(int(r["TB_EVTNR"]), r["TB_TAXTP"]) for r in rows}
        for row in rows:
            self.book(row)

    def book(self, row):
        """Calculates one booking and files it per payout event and per year.

        An unknown tax type, or a payout tax whose event is no counted payout, books nothing.
        """
        kind, event = row["TB_TAXTP"], int(row["TB_EVTNR"])
        payout = self.payouts.get(event)
        amount = getattr(self, CALCULATE[kind])(row, payout) if self.calculable(kind, event, payout) else Decimal(0)
        self.amounts[event, kind] = self.amounts.get((event, kind), Decimal(0)) + amount
        self.annual.append((parts(row["TB_EFFDT"])[0], kind, amount))
        if amount and event not in self.countries:
            self.countries[event] = self.rate(row)["TX_CNTRY"]

    @staticmethod
    def calculable(kind, event, payout):
        """A known tax type on its own kind of event: a counted payout, or for OWN_EVENT its premium or event 0.

        Anything else (an unknown type, a reversed payout) books nothing instead of failing.
        """
        own = kind == OWN_EVENT[0] or kind in OWN_EVENT and not event
        return kind in CALCULATE and bool(payout or own)

    def rate(self, row, region=""):
        """The NRTAXR row of a booking's tax type on its date, as known when it was booked.

        BOC uses the rows of BOL, the tax it collects.
        """
        kind = COLLECTS.get(row["TB_TAXTP"], row["TB_TAXTP"])
        return tax_rate(self.legacy_dir, kind, region, row["TB_EFFDT"], row["TB_CHGTS"])

    def percent(self, row, region=""):
        """The rate of a booking as a number, 0 when the tax did not exist on its date.

        TX_RATE is N(6): 250000 is 25 %.
        """
        rate = self.rate(row, region)
        return num(rate["TX_RATE"], 6) if rate else Decimal(0)

    def taxed(self, row, base, region=""):
        """The tax on a base, rounded in the era of the booking.

        COBOL Neuron cut the cents (77.38 in the PDF example), Java Neuron rounds half up.
        """
        return tax_cents(self.policy, base * self.percent(row, region), row["TB_EFFDT"])

    def converted(self, row, amount, legacy_date):
        """An amount of the policy currency in the currency of a booking's tax, at the rate of the date.

        The tax currency follows the country of the tax (TX_CNTRY).
        """
        return exchange(self.policy, amount, tax_currency(self.rate(row)["TX_CNTRY"]), legacy_date, legacy_date)

    def withheld(self, row, base):
        """A tax withheld from a payout; its base is kept for the payout row.

        The base is the taxable_base column of t7_tax_payout.
        """
        self.bases[int(row["TB_EVTNR"])] = base
        return self.taxed(row, base)

    def premium_stamp(self, row, _):
        """STP: Swiss stamp duty on a single premium, in francs on the day it was received.

        Booked for Swiss residents' single premiums from 1998-04-01 (NRTAXR).
        """
        item = next(p for p in grouped(self.legacy_dir, "NRPREM", "PR_POLNR")[self.policy.policy_id]
                    if p["PR_EVTNR"] == row["TB_EVTNR"])
        fx_date = premium_trades(self.legacy_dir)[self.policy.policy_id, int(row["TB_EVTNR"])] \
            if STP_FX_DATE == "traded" else item[STP_COLUMNS[STP_FX_DATE][0]]
        booked = row["TB_EFFDT"] if STP_ROUNDING == "converted" else None
        currency = tax_currency(self.rate(row)["TX_CNTRY"])
        premium = exchange(self.policy, num(item[STP_COLUMNS[STP_AMOUNT][1]], 2), currency, fx_date, booked)
        return self.taxed(row, premium)

    def payout_tax(self, row, payout):
        """VST: Swiss withholding tax on the whole payout.

        Booked when the holder objected to reporting (tax status E) and the payout exceeds TX_THRSH.
        """
        return self.withheld(row, self.converted(row, payout.paid(self.policy), payout.date))

    def gain_tax(self, row, payout):
        """SOS: Italian substitute tax, each part of the gain at the rate of the period it accrued in.

        A rate change (a new NRTAXR version: 12.5 % to 2011, 20 % to 2014-06-30, 26 % since) splits the holding
        period at the day before it; a period's gain is the policy value at its end less the value at its start and
        the premiums paid in it, a loss in one period raising the next one's (samples: effective rates 16 % to 27 %).
        The taxable_base shown stays the whole gain. Not booked for death claims or losses.
        """
        self.bases[payout.event] = tax_cents(self.policy, payout.taxable_gain, row["TB_EFFDT"])
        tax, start_value = Decimal(0), Decimal(0)
        for start, end in self.periods(row, payout):
            end_value = self.remaining_value(row, payout, end)
            gain = end_value - start_value - self.premiums_in(payout, start, end)
            tax, start_value = tax + gain * self.percent(dict(row, TB_EFFDT=str(end))), end_value
        return tax_cents(self.policy, tax * payout.share, row["TB_EFFDT"])

    def periods(self, row, payout):
        """[(after, until)] of the rate periods from the policy start to the payout: a new rate version from a day
        after the start splits at the day before."""
        start = int(self.policy.first["PH_BEGDT"]) - 1
        versions = known(readable_rates(self.legacy_dir).get(row["TB_TAXTP"], []), "TX", row["TB_CHGTS"])
        changes = sorted({legacy(day(r["TX_VLDFR"]) - dt.timedelta(days=1)) for r in versions})
        ends = [d for d in changes if start < d < payout.date] + [payout.date]
        return list(zip([start] + ends[:-1], ends))

    def remaining_share(self, payout, legacy_date):
        """The part of what existed on a date that earlier withdrawals of the policy have not taken out yet."""
        share = Decimal(1)
        for earlier in self.payouts.values():
            if (earlier.date, earlier.event) < (payout.date, payout.event) and legacy_date <= earlier.date:
                share *= 1 - earlier.share
        return share

    def remaining_value(self, row, payout, legacy_date):
        """The policy value at a period end in the tax currency, the part not withdrawn before; at the payout itself
        the value it was paid from (payout / share)."""
        if legacy_date == payout.date:
            return payout.amount / payout.share
        return self.year_end_value(dict(row, TB_EFFDT=str(legacy_date))) * self.remaining_share(payout, legacy_date)

    def premiums_in(self, payout, after, until):
        """The premiums received in a period, in the tax currency, the part not given back by earlier withdrawals."""
        currency = tax_currency(payout.country)
        return sum((exchange(self.policy, amount, currency, received, received)
                    * self.remaining_share(payout, received)
                    for received, amount in premium_items(self.policy) if after < received <= until), Decimal(0))

    def capital_gains_tax(self, row, payout):
        """KST: German capital gains tax on the taxable share of the gain.

        1 less the partial exemption (TFS, from 2018), halved by the half-income rule (HEV) when it applies.
        """
        share = 1 - (self.percent(dict(row, TB_TAXTP="TFS")) if PARTIAL_EXEMPTION else 0)
        if self.half_income(payout):
            share *= self.percent(dict(row, TB_TAXTP="HEV"))
        base = tax_cents(self.policy, payout.taxable_gain * share, row["TB_EFFDT"])
        self.bases[payout.event] = base
        return tax_cents(self.policy, base * self.percent(row) / self.church_deduction(row), row["TB_EFFDT"])

    def church_deduction(self, row):
        """1, or with CHURCH_TAX "deductible" and church tax booked: 1 + KST rate x church rate of the region."""
        if CHURCH_TAX != "deductible" or (int(row["TB_EVTNR"]), "KIS") not in self.booked:
            return 1
        address = residence(self.legacy_dir, self.policy.policy_id, row["TB_EFFDT"], row["TB_CHGTS"])
        return 1 + self.percent(row) * self.percent(dict(row, TB_TAXTP="KIS"), address["AD_REGIO"].strip())

    def half_income(self, payout):
        """The half-income rule (German law, not visible in the data).

        A policy started from HEV_FROM, held at least HEV_YEARS and paid out when the holder is at least the age for
        its start (HEV_AGES: 62 from 2012, 60 before).
        """
        start = int(self.policy.first["PH_BEGDT"])
        person = grouped(self.legacy_dir, "NRPERS", "PS_PERNR")[payout.address["AD_PERNR"].strip()][0]
        age = next(a for since, a in HEV_AGES if start >= since)
        return start >= HEV_FROM and age_on(start, payout.date) >= HEV_YEARS and age_on(person["PS_BIRTH"],
                                                                                        payout.date) >= age

    def surcharge(self, row, _):
        """SOL, KIS: a share of the capital gains tax of the same payout, at the rate of the holder's region.

        Church tax only for church members, from 2009 (NRTAXR).
        """
        address = residence(self.legacy_dir, self.policy.policy_id, row["TB_EFFDT"], row["TB_CHGTS"])
        tax = self.amounts.get((int(row["TB_EVTNR"]), SURCHARGED), Decimal(0))
        return cents(tax * self.percent(row, address["AD_REGIO"].strip()), cobol=True)

    def stamp_duty(self, row, payout):
        """BOL: Italian stamp duty at a final payout, at a year end, or a restatement of the earlier ones.

        Every amount adds to the stamp duty a later payout collects.
        """
        if payout:
            amount = self.accrue(row, self.prorated(row, payout))
        elif parts(row["TB_EFFDT"])[1:] == YEAR_END:
            amount = self.accrue(row, self.year_end_value(row) * self.first_year_share(row))
        else:
            amount = self.restated(row)
        self.stamp_duties += amount
        return amount

    def accrue(self, row, base):
        """Stamp duty on a base, kept so that a later restatement can recalculate it.

        The base is the value in the tax currency (pro rata at a final payout).
        """
        self.accrued[row["TB_EFFDT"]] = [base, row["TB_CHGTS"]]
        return self.taxed(row, base)

    def restated(self, row):
        """A restatement: every earlier stamp duty's base times its rate as known now less the rate it was booked
        at, summed and rounded once (e.g. IT BOL 2017-2019 restated in 2019 as version 2: 0.15 % became 0.2 %).

        Samples: rounding once fits every 2019 row, rounding per year is a cent off on some; PDF 616.11 either way.
        """
        change = Decimal(0)
        for accrued_on, (base, booked) in self.accrued.items():
            then = self.percent({**row, "TB_EFFDT": accrued_on, "TB_CHGTS": booked})
            change += base * (self.percent(dict(row, TB_EFFDT=accrued_on)) - then)
            self.accrued[accrued_on][1] = row["TB_CHGTS"]
        return tax_cents(self.policy, change, row["TB_EFFDT"])

    def year_end_value(self, row):
        """The policy value on the date in the tax currency: units at the bid per fund and pot, as in t3.

        From the shared replay (neuron/funds/replay.py), converted at the FX of the date.
        """
        account, d = self.replayed[self.policy.policy_id], int(row["TB_EFFDT"])
        holdings = account.holdings(d).items()
        return self.converted(row, sum((pot_value(self.policy, f, units, d, d) for (f, _), units in holdings),
                                       Decimal(0)), d)

    def first_year_share(self, row):
        """1, or with BOL_FIRST_YEAR "prorated" in the policy's first year: its days from the start over the year."""
        year_end = day(row["TB_EFFDT"])
        if BOL_FIRST_YEAR != "prorated" or self.policy.start.year != year_end.year:
            return 1
        return Decimal((year_end - self.policy.start).days + 1) / year_end.timetuple().tm_yday

    def prorated(self, row, payout):
        """The value paid out at a final payout, for the days of its year up to the payout day.

        Days since 31 December over the days of the year.
        """
        paid_on = day(payout.date)
        value = self.converted(row, payout.sold, payout.date)
        if BOL_FINAL_DAYS == "since_start":
            since = max(dt.date(paid_on.year, 1, 1), self.policy.start)
            return value * (paid_on - since).days / YEAR_DAYS
        return value * paid_on.timetuple().tm_yday / dt.date(paid_on.year, *YEAR_END).timetuple().tm_yday

    def collect(self, row, payout):
        """BOC: the payout's share of the stamp duty accrued and not collected yet.

        A withdrawal leaves the rest for later payouts, a surrender or death claim collects it all.
        """
        amount = tax_cents(self.policy, payout.share * (self.stamp_duties - self.collected), row["TB_EFFDT"])
        self.collected += amount
        return amount


@functools.cache
def premium_trades(legacy_dir):
    """{(policy_id, premium event): first trade date of its PRM bookings}, read from NRBOOK only for STP_FX_DATE
    "traded"."""
    trades = {}
    with open(pathlib.Path(legacy_dir, "NRBOOK.csv"), encoding="utf-8-sig") as f:
        header = next(f).rstrip("\r\n").split(";")
        policy, event, kind, traded = map(header.index, ("BK_POLNR", "BK_EVTNR", "BK_BKTYP", "BK_TRDDT"))
        for row in (line.split(";") for line in f if ";PRM;" in line):
            if row[kind] == "PRM" and (key := (row[policy].strip(), guarded(int, row[event]))) not in trades:
                trades[key] = row[traded]
    return trades


@functools.cache
def ledgers(legacy_dir):
    """{policy_id: Ledger} of every policy with a payout or a tax booking; incomplete ones are left out.

    The shared replay is asked once here: if it failed, only the policies needing a year-end value are left out.

    Calculated once per export and shared by both t7 functions.
    """
    events = grouped(legacy_dir, "NREVNT", "EV_POLNR").items()
    with_payouts = {p for p, rows in events if any(e["EV_EVTTP"] in PAYOUT_EVENTS for e in rows)}
    policies = sorted(with_payouts | set(grouped(legacy_dir, "NRTAXB", "TB_POLNR")))
    replayed = guarded(accounts, legacy_dir) or {}
    return {p: ledger for p in policies if (ledger := guarded(Ledger, legacy_dir, p, replayed))}
