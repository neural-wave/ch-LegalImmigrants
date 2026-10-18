"""The fund accounting of a policy (t3 and t4): its bookings replayed with their missing amounts.

Trades are replayed in Neuron's order (bookings.py); premiums and monthly charge runs get their amounts and units,
customer orders keep theirs. The result per policy is an Account, replayed once per export and shared by the tasks:
the units of every pot over time and the yearly premiums and charges.

PRM bookings: a received premium, less the entry charge, buys fund units at the issue price (ask). The premium is
split by the allocation (NRALLO) valid on the money date, at the entry rate of that date (an ENT agreement, else the
NRENTC rate of the broker tier). It converts at the FX of the day before the trade, unrounded; investment.py books
each fund.

The monthly charge run (ADM, AMC, RSK), whose amounts Neuron's nightly job left blank in NRBOOK. Amounts are in the
policy currency, rounded to the cent; units have 6 decimals. Both are rounded half up by Java Neuron and truncated by
COBOL Neuron (trade dates before the conversion). FX is never rounded. In order: the admin fee shared by value
(`split`), the management charge per pot (management_fee.py), then the risk charge on what is left (left_value.py,
`risk_charge`), shared by those left values.

The Account: t3 values the units on a valuation date (holdings.py), t4 reads the calendar-year totals. Premiums count
in the year of their money date (premium_dates.py); entry charges (per fund) and monthly charges in the year of their
trade date (statement_entry.py).
"""
import collections
import functools
from decimal import Decimal

from neuron.calendar.eve import eve
from neuron.cobol import is_cobol
from neuron.contract import contract
from neuron.cyymmdd import parts
from neuron.data import CHARGES, PREMIUM, guarded, num
from neuron.funds.accrual import accrual
from neuron.funds.bookings import read_bookings, trades
from neuron.funds.cancellation import cancelled_units
from neuron.funds.holdings import units_on
from neuron.funds.investment import invest
from neuron.funds.left_value import left_after
from neuron.funds.management_fee import management_fee
from neuron.funds.position import booked
from neuron.funds.premium_dates import premium_dates
from neuron.funds.pro_rata import pro_rata
from neuron.funds.remainder import with_remainder
from neuron.funds.statement_entry import statement_entry
from neuron.terms.age import age
from neuron.terms.death_rate import death_rate
from neuron.terms.monthly_risk import monthly_risk
from neuron.terms.net_premium import net_premium
from neuron.terms.rates import allocation, charges, entry_rate, management_rate
from neuron.valuation import valued


def invest_premium(policy, rows, holdings):
    """Amount, entry charge, price and units of the PRM bookings of one premium trade.

    `holdings` is not needed: a premium doesn't depend on what the policy holds (same call as take_charges).
    """
    paid, traded = rows[0].money_date, rows[0].trade_date
    premium, shares = policy.premiums[rows[0].event], allocation(policy, paid)
    invested, converted = net_premium(premium, entry_rate(policy, paid)), eve(traded)
    for row in rows:
        row.price = policy.market.ask(row.fund, row.price_date)
        fx = policy.market.fx(policy.currency, row.fund, converted)
        invest(policy, row, premium, invested, shares.get(row.fund, 0), fx, traded)


def split(charge, values, cents):
    """{(fund, pot): share} of `charge` over the pots' `values`, adding up to the charge (or to the values).

    Shared in proportion to the values (pro_rata.py), at most the sum of the values: a policy running out of value
    pays what it has left, every pot what it holds. The remainder of the rounding goes to the largest pot
    (remainder.py). Pots without value share nothing.
    """
    whole = sum(values.values())
    if whole:
        charge = min(charge, whole)
        return with_remainder(pro_rata(charge, values, whole, cents), values, charge)
    return dict.fromkeys(values, Decimal(0))


def risk_charge(policy, tariff, left, traded):
    """The risk charge (RSK) of a run, before rounding: one month of risk (monthly_risk.py) on the value left after
    the admin fee and the management charge, all pots together, at the death probability of the insured's age in
    the policy year of the run (age.py); `split` shares it by the left values."""
    return monthly_risk(policy, sum(left.values()), death_rate(policy, tariff, age(policy, traded)))


def charge_amounts(policy, values, event, traded, cents):
    """{kind: {(fund, pot): amount}} of one charge run, on the values (policy currency) before it."""
    tariff = charges(policy, traded)
    period = accrual(policy, event, is_cobol(traded, policy.cobol_until))
    admin = split(num(tariff["CG_ADMFEE"], 2), values, cents)
    rates = {pot: management_rate(policy, pot, tariff, traded) for pot in {pot for _, pot in values}}
    management = {k: management_fee(v, rates[k[1]], period, cents) for k, v in values.items()}
    left = left_after(values, admin, management)
    risk = split(cents(risk_charge(policy, tariff, left, traded)), left, cents)
    return {"ADM": admin, "AMC": management, "RSK": risk}


def quotes(policy, rows, pots):
    """{fund: (bid, FX)} of the funds of a run, looked up once per fund and shared by its pots and rows.

    A fund is priced on the price date of its rows, a held fund without a row on the run's first price date.
    """
    priced, traded, market = {row.fund: row.price_date for row in rows}, rows[0].trade_date, policy.market
    return {fund: (market.bid(fund, priced.get(fund, rows[0].price_date)), market.fx(policy.currency, fund, traded))
            for fund in {fund for fund, _ in pots}}


def take_charges(policy, rows, holdings):
    """Monthly ADM, AMC and RSK, cancelled at the redemption price in all funds and pots the policy holds.

    Each pot is valued at the bid of its own price date and the FX of the trade date, rounded to the cent. A pot
    whose charge rounds to 0.00 has no booking, but its value still counts in the shares of the others. Pots with a
    row come first, in file order: on equal values the first one takes the rest of a split (BL10002262, 2019-12).
    """
    traded = rows[0].trade_date
    pots = dict.fromkeys([*(row.key for row in rows), *(k for k, units in holdings.items() if units)])
    quoted, (cents, units) = quotes(policy, rows, pots), policy.rounders(traded)
    values = {k: valued(holdings[k], *quoted[k[0]], cents) for k in pots}
    amounts = charge_amounts(policy, values, rows[0].event, traded, cents)
    for row in rows:
        row.price, fx = quoted[row.fund]
        row.amount = amounts[row.kind][row.key]
        row.units = cancelled_units(row.amount, fx, row.price, units)


TRADES = {PREMIUM: invest_premium, **dict.fromkeys(CHARGES, take_charges)}  # customer orders keep their units


def replay(policy, bookings):
    """(rows, timeline): all counted bookings of a policy in trade order, with their amounts and units calculated,
    and {(fund, pot): {trade date: units after the trades of that date}}, dates in trade order.

    The holdings run along: a charge run takes its charges from every pot held just before it.
    """
    holdings, timeline, done = collections.defaultdict(Decimal), collections.defaultdict(dict), []
    for rows in trades(bookings, policy.skipped):
        if book := TRADES.get(rows[0].kind):
            book(policy, rows, holdings)
        for row in rows:
            timeline[row.key][row.trade_date] = booked(holdings, row)  # of several trades on a day the last counts
        done.extend(rows)
    return done, timeline


class Account:
    """What the tasks need from a replayed policy.

    timeline: {(fund, pot): {trade date: units after the trades of that date}}, dates in trade order
    totals: {(year, PRM / ENT / ADM / AMC / RSK): amount}
    """

    def __init__(self, policy, rows, timeline):
        self.policy, self.timeline, amounts = policy, timeline, {}
        for row in rows:
            if entry := statement_entry(row):
                column, amount = entry
                amounts.setdefault((parts(row.trade_date)[0], column), []).append(amount)
        for event, paid in premium_dates(rows).items():
            amounts.setdefault((parts(paid)[0], "PRM"), []).append(policy.premiums[event])
        self.totals = collections.defaultdict(Decimal, {key: sum(values) for key, values in amounts.items()})

    def holdings(self, legacy_date):
        """{(fund, pot): units} after the trades up to and including the date."""
        return {key: units_on(after, legacy_date) for key, after in self.timeline.items()}


def account(legacy_dir, policy_id, bookings):
    """(policy_id, Account) of one policy from its NRBOOK rows."""
    policy = contract(legacy_dir, policy_id)
    return policy_id, Account(policy, *replay(policy, bookings))


@functools.cache
def accounts(legacy_dir):
    """{policy_id: Account} of every policy in the export, replayed once and shared by t3 and t4.

    A policy whose data is incomplete is left out, so the other policies of a private export still get their values.
    """
    return dict(filter(None, (guarded(account, legacy_dir, *policy) for policy in read_bookings(legacy_dir))))
