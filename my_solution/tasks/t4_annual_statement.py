"""t4 annual statement: premiums and charges per policy and calendar year (same charges as t3).

The amounts are the yearly totals of the replayed bookings (neuron/funds/): premiums in the year of their money date,
the entry charge (what the funds didn't get of a premium) and the monthly charges in the year of their trade date.
A policy gets a statement for every year from its start to the year it ended by surrender or death, at the latest the
last full year before the extract.
"""
from decimal import Decimal

from neuron.funds.replay import accounts
from neuron.statement_years import statement_years

COLUMNS = ("PRM", "ENT", "ADM", "AMC", "RSK")


def statement(totals, year):
    """(premiums, entry, admin, management, risk, total charges) of one year."""
    premiums, *charges = (totals[year, column] for column in COLUMNS)
    return (premiums, *charges, sum(charges))


def t4_annual_statement(legacy_dir) -> dict[tuple[str, int], tuple[Decimal, ...]]:
    """{(policy_id, year): (premiums, entry_charges, admin_fees, management_fees, risk_charges, total_charges)}"""
    return {(policy_id, year): statement(account.totals, year)
            for policy_id, account in accounts(legacy_dir).items() for year in statement_years(account.policy)}
