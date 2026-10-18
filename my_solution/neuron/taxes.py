"""Neuron's tax module (t7): residence, tax rates and payouts as the module saw them.

What the module knew
    It used what it knew when it booked. A holder or address change recorded later (HD_CHGTS, AD_CHGTS) and a rate
    version entered later (TX_CHGTS) did not count yet: an address change recorded in March does not move a year-end
    stamp duty booked in January. Each tax type belongs to one country of NRTAXR, which also sets the currency of
    the tax: francs in Switzerland, euro elsewhere.

What a payout is
    What the customer was paid: a withdrawal or surrender net of the surrender penalty, a death claim with the sum
    at risk of its death benefit option. Its gain is the payout less the premiums it gives back, both in the tax
    currency at the rate of their own day and rounded in the era of the payout. A withdrawal gives back its share
    (EV_PCTG) of every premium still invested, a surrender or death claim all of it.

Evidence (lab, presence of NRTAXB bookings)
    A German or Italian payout was taxed exactly when this gain is positive (627 of 628 payouts that no exemption
    covers). Converting the gain at the payout date only, or giving back all premiums on a withdrawal, or ignoring
    the surrender penalty all fit far worse. Before the euro existed (1999), its first rate converts the premiums.
"""
import bisect
import csv
import functools
import pathlib
from decimal import Decimal

from neuron.contract import cents
from neuron.data import as_of, grouped, guarded, num
from neuron.funds.bookings import read_bookings
from neuron.reversals import skipped_events
from neuron.terms.death_benefit import sum_at_risk
from neuron.terms.net_of_penalty import net_of_penalty
from neuron.valuation import pot_value

TAX_CURRENCY, EURO = {"CH": "CHF"}, "EUR"  # Switzerland taxes in francs, Italy, Germany and Luxembourg in euro
TAX_CURRENCIES = (EURO, *TAX_CURRENCY.values())
WITHDRAWAL, SURRENDER, DEATH = "400", "410", "500"  # NRCODE EVTTP of the payouts
PAYOUT_EVENTS = (WITHDRAWAL, SURRENDER, DEATH)
PAYOUT_BOOKINGS = ("WDR", "SUR", "DTH")  # NRCODE BKTYP: units sold for a payout
# Before the euro existed (1999) a premium is converted with the EUR rate of its first date and the policy currency
# at the receipt date ("eur_first"), or both at the first EUR date ("both_first", explains BL10000551 #67 untaxed)
PRE_EURO = "both_first"  # upload 4: removes the one NRTAXB presence mismatch; "eur_first" was uploads 1-3
# Rounding of the tax module: "era" (COBOL cut before 2007-08-11, Java half up after, as in t0-t4; PDF: 2006 cut,
# 2019 BOL half up) or "cut" (the tax module kept COBOL's cut after the conversion)
TAX_ROUNDING = "era"
# Where the payout orders come from: "replay" (the units of the WDR/SUR/DTH bookings as the fund replay reads them,
# valued at bid / FX; the board reads NRBOOK this way correctly, t3 100 %) or "nrbook" (BK_AMTPC via paid_out(), the
# replay only as a fallback). Both give the same orders on train; on the board's sample 3 "nrbook" failed.
PAYOUT_SOURCE = "replay"
DEATH_PAYOUT = "benefit"  # samples: CH deaths = 101 % of the value (option A); "value" = the DTH value only
ORDER_COLUMNS = ("BK_POLNR", "BK_EVTNR", "BK_BKTYP", "BK_FNDID", "BK_UNITS", "BK_PRCDT", "BK_TRDDT", "BK_AMTPC")
NOT_A_PAYOUT = ()  # what payout_line returns for an NRBOOK line of another booking type


def known(rows, prefix, timestamp):
    """The versions of a table already entered at a processing timestamp (CHGTS)."""
    return [r for r in rows if int(r[f"{prefix}_CHGTS"]) <= int(timestamp)]


def residence(legacy_dir, policy_id, legacy_date, timestamp):
    """The NRADDR row of the policyholder on a date, holder and address both as known at the timestamp.

    The holder is NRHOLD's person, not always the insured; the address carries country, region, tax status and
    church membership.
    """
    holders = known(grouped(legacy_dir, "NRHOLD", "HD_POLNR")[policy_id], "HD", timestamp)
    person = as_of(holders, "HD", legacy_date)["HD_PERNR"].strip()
    return as_of(known(grouped(legacy_dir, "NRADDR", "AD_PERNR")[person], "AD", timestamp), "AD", legacy_date)


def tax_rate(legacy_dir, tax_type, region, legacy_date, timestamp):
    """The NRTAXR row of a tax type on a date as known at the timestamp.

    A row for the holder's region (church tax in Bavaria and Baden-Wuerttemberg) wins over the row for all regions
    (blank TX_REGIO). None when the tax did not exist on the date.
    """
    rows = known(readable_rates(legacy_dir).get(tax_type, []), "TX", timestamp)
    regional = as_of([r for r in rows if r["TX_REGIO"].strip() == region], "TX", legacy_date)
    return regional or as_of([r for r in rows if not r["TX_REGIO"].strip()], "TX", legacy_date)


def rate_version(row):
    """The validity, version, entry time and rate of an NRTAXR row; fails for an unreadable one."""
    keys = ("TX_VLDFR", "TX_VLDTO", "TX_CHGTS")
    return (*(int(row[k]) for k in keys), int(row["TX_VRSNR"] or 0), num(row["TX_RATE"], 6))


@functools.cache
def readable_rates(legacy_dir):
    """{tax type: NRTAXR rows} without the unreadable rows.

    A broken rate row is left out instead of failing every policy taxed at that type: the other versions apply.
    """
    rates = grouped(legacy_dir, "NRTAXR", "TX_TAXTP")
    return {kind: [r for r in rows if guarded(rate_version, r)] for kind, rows in rates.items()}


def tax_currency(country):
    """The currency a country's taxes are booked in."""
    return TAX_CURRENCY.get(country, EURO)


def tax_cents(policy, amount, legacy_date):
    """Money of the tax module rounded to the cent by TAX_ROUNDING."""
    return policy.cents(amount, legacy_date) if TAX_ROUNDING == "era" else cents(amount, cobol=True)


def chf_rate(market, currency, legacy_date):
    """CHF per unit of a currency on a date, the last rate on or before it.

    Before a currency's first rate (EUR before 1999) Neuron took that first rate.
    """
    dates, values = market.rates[currency]
    return values[max(bisect.bisect_right(dates, int(legacy_date)) - 1, 0)]


def exchange(policy, amount, currency, legacy_date, booked):
    """An amount of the policy currency in another currency.

    At the rate of its own date, crossed via CHF, rounded in the era of the day it was booked: COBOL Neuron cut the
    cents, Java Neuron rounds half up. booked None: not rounded.
    """
    if PRE_EURO == "both_first":
        legacy_date = max(int(legacy_date), policy.market.rates[currency][0][0])
    rate = chf_rate(policy.market, policy.currency, legacy_date) / chf_rate(policy.market, currency, legacy_date)
    return amount * rate if booked is None else tax_cents(policy, amount * rate, booked)


@functools.cache
def paid_out(legacy_dir):
    """({(policy_id, event): [(fund, units, price date, trade date, amount sold or None)]}, {broken policy_id}).

    Reads NRBOOK once more with the csv module (quoted or plain fields alike), columns by header name, but parses only
    the lines that mention a payout booking type. A line whose key or units can't be read costs only its policy.
    """
    orders, broken = {}, set()
    with open(pathlib.Path(legacy_dir, "NRBOOK.csv"), encoding="utf-8-sig", newline="") as f:
        header = [name.strip() for name in next(csv.reader([next(f)], delimiter=";"))]
        columns = tuple(map(header.index, ORDER_COLUMNS))
        lines = (line for line in f if any(kind in line for kind in PAYOUT_BOOKINGS))
        for row in csv.reader(lines, delimiter=";"):
            decoded = guarded(payout_line, row, columns)
            if decoded is None and len(row) > columns[0]:
                broken.add(row[columns[0]].strip())
            elif decoded:
                orders.setdefault(decoded[0], []).append(decoded[1])
    return orders, broken


def payout_line(row, columns):
    """((policy_id, event), (fund, units, price date, trade date, amount sold)) of an NRBOOK payout line, NOT_A_PAYOUT
    for another booking type. The amount is None when BK_AMTPC is blank or unreadable (Payout then values the units).
    """
    policy, event, kind, fund, units, priced, traded, amount = (row[c].strip() for c in columns)
    if kind not in PAYOUT_BOOKINGS:
        return NOT_A_PAYOUT
    sold = guarded(num, amount, 2) if amount else None
    return (policy, int(event)), (fund, num(units, 6), int(priced), int(traded), None if sold is None else -sold)


def payout_orders(legacy_dir, policy_id, event):
    """The orders of a payout event: from paid_out(), or, when that reader fails or has none for the event, from the
    bookings the fund replay reads (read_bookings, the reader t3 and t4 use), valued from their units by sold()."""
    if PAYOUT_SOURCE == "replay":
        return replay_orders(legacy_dir).get((policy_id, event), [])
    orders, broken = payout_reading(legacy_dir)
    found = orders.get((policy_id, event)) if policy_id not in broken else None
    return found or replay_orders(legacy_dir).get((policy_id, event), [])


@functools.cache
def payout_reading(legacy_dir):
    """paid_out(), or no orders when it fails for any reason; cached either way, so NRBOOK is read once by it."""
    try:
        return paid_out(legacy_dir)
    except Exception:  # noqa: BLE001 - any file the payout reader can't parse falls back to the replay's reader
        return {}, set()


@functools.cache
def replay_orders(legacy_dir):
    """{(policy_id, event): [(fund, units, price date, trade date, None)]} of the payout bookings as the fund replay
    reads them (read only if paid_out() missed something)."""
    orders = {}
    for policy_id, bookings in read_bookings(legacy_dir):
        for b in bookings or []:
            if b.kind.strip() in PAYOUT_BOOKINGS:
                orders.setdefault((policy_id, b.event), []).append((b.fund, b.units, b.price_date, b.trade_date, None))
    return orders


def sold(policy, orders):
    """The amount the payout orders sold, in the policy currency: BK_AMTPC, or where it is missing the units at the
    bid of the price date over the FX of the trade date, rounded like Neuron (the same as BK_AMTPC on train)."""
    return sum((-pot_value(policy, fund, units, priced, traded) if amount is None else amount
                for fund, units, priced, traded, amount in orders), Decimal(0))


class Payout:
    """One payout event of a policy: date, share, the holder's residence, what was paid and its gain.

    amount: the payout in the tax currency of the residence; gain: set by `payouts` (it needs the earlier payouts).
    """

    def __init__(self, policy, event):
        row = policy.events[event]
        self.event, self.date, self.timestamp = event, int(row["EV_EFFDT"]), row["EV_CHGTS"]
        self.kind, self.share = row["EV_EVTTP"], num(row["EV_PCTG"], 6)
        self.address = residence(policy.legacy_dir, policy.policy_id, self.date, self.timestamp)
        self.country = self.address["AD_CNTRY"].strip()
        self.sold = sold(policy, payout_orders(policy.legacy_dir, policy.policy_id, event))
        self.amount = exchange(policy, self.paid(policy), tax_currency(self.country), self.date, self.date)
        self.gain = Decimal(0)

    def paid(self, policy):
        """What the customer got in the policy currency: the death benefit, or the value net of the penalty."""
        if self.kind == DEATH and DEATH_PAYOUT == "value":
            return self.sold
        if self.kind == DEATH:
            return self.sold + tax_cents(policy, Decimal(sum_at_risk(policy, self.sold)), self.date)
        return net_of_penalty(policy, self.date, self.sold)

    @property
    def taxable_gain(self):
        """The gain, 0 for a loss."""
        return max(self.gain, Decimal(0))


def premium_items(policy):
    """[(receipt date, amount)] of the premiums received: NRPREM items whose booking event counts.

    A returned direct debit or a written-off item has no counted event, so it gives nothing back.
    """
    counted = set(policy.events) - skipped_events(policy.events)
    items = grouped(policy.legacy_dir, "NRPREM", "PR_POLNR").get(policy.policy_id, [])
    return [(int(p["PR_RCVDT"]), num(p["PR_AMTRC"], 2)) for p in items if int(p["PR_EVTNR"]) in counted]


def paid_in(policy, items, currency, legacy_date):
    """The premiums received up to a date in a currency, each converted at the rate of its receipt date and rounded
    in the era of that date (COBOL cut before the conversion, PDF example; samples: Java payouts of older policies)."""
    return sum((exchange(policy, amount, currency, received, received) for received, amount in items
                if received <= legacy_date), Decimal(0))


def payouts(policy):
    """[Payout] of a policy in date order, each with its gain over the premiums it gives back.

    A payout gives back its share (EV_PCTG) of the premiums not given back yet: that cost is rounded to the cent and
    kept as money, per tax currency, so later payouts start from the premiums paid less the costs before them
    (samples: withdrawal costs rounded, BL10000670 and BL10001775; BL10003541 after two withdrawals).
    """
    events = {n for n, e in policy.events.items() if e["EV_EVTTP"] in PAYOUT_EVENTS} - skipped_events(policy.events)
    done = sorted((Payout(policy, n) for n in events), key=lambda p: (p.date, p.event))
    items, given_back = premium_items(policy), dict.fromkeys(TAX_CURRENCIES, Decimal(0))
    for payout in done:
        costs = {currency: tax_cents(policy, payout.share * (paid_in(policy, items, currency, payout.date) - back),
                                     payout.date) for currency, back in given_back.items()}
        payout.gain = payout.amount - costs[tax_currency(payout.country)]
        given_back = {currency: given_back[currency] + cost for currency, cost in costs.items()}
    return done
