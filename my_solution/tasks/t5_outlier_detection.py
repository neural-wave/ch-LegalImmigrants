"""t5 outlier detection: values that were changed by hand and follow no rule.

A manual correction moves one value by a whole, non-zero amount (t0 +9 to +77, t2 ±1,000s, t3 and t4 +7 to +499) and
leaves everything else as the rules made it. A target value is therefore flagged when it differs from the value our
rules give by whole euros. Rows a rule only misses by cents are rule gaps, not hand edits.

t0 and t2 are compared with their task functions. t3 and t4 are checked on the target files alone (below),
on the only columns Neuron's corrections ever touch (NREXCP): the surrender value and the admin fees. That needs no
fund accounting, so a gap in it can't look like a hand edit:

- t3: the surrender value is the target's own policy value less the surrender penalty (neuron/terms/rates.py),
- t4: the admin fees of a year are the tariff's monthly fee for every monthly charge run (event 300) of that year.

Target files are read in the format of `targets/`; keys come back in the submission format, so t5's flags match the
scorer's keys. This is the only task that may read them. t1 is not checked: its targets have no corrections.
"""
import csv
import datetime as dt
import functools
import pathlib
from decimal import Decimal

from neuron.charge_runs import charge_runs
from neuron.contract import contract
from neuron.data import day, guarded, num
from neuron.hand_edits import hand_edited
from neuron.legacy import legacy
from neuron.terms.net_of_penalty import net_of_penalty
from neuron.terms.rates import charges
from tasks.t0_commission import t0_commission
from tasks.t2_projected_maturity_value import t2_projected_maturity_value

# task -> converters of its key columns, in target file order; the value columns follow the keys
KEYS = {
    "t0_commission": (str, int),
    "t2_projected_maturity_value": (str,),
    "t3_surrender_value": (str, dt.date.fromisoformat),
    "t4_annual_statement": (str, int),
}
ADMIN_FEES = 2  # column of the admin fees in an annual statement row
RULES = {"t0_commission": t0_commission, "t2_projected_maturity_value": t2_projected_maturity_value}


def read_targets(targets_dir, task):
    """{key: [value columns as Decimal]} of a target file.

    {} when the file is not there: a private set without a task's file has nothing to check for it.
    """
    path = pathlib.Path(targets_dir, f"{task}.csv")
    rows = read_rows(path) if path.exists() else []
    width = len(KEYS[task])
    return {key(task, row[:width]): [Decimal(v) for v in row[width:]] for row in rows}


def read_rows(path):
    """The rows of a CSV file without its header."""
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.reader(f))[1:]


def key(task, parts):
    """A target key in the submission format: the policy id alone, or a tuple with its second key.

    t5 returns its keys in this format, so the scorer matches them with the task's own keys.
    """
    values = tuple(convert(p) for convert, p in zip(KEYS[task], parts))
    first, *more = values
    return values if more else first


def surrender_value(legacy_dir, policy_id, valuation, policy_value):
    """A target's policy value (0 if negative) less the surrender penalty, rounded like Neuron on that date."""
    return net_of_penalty(contract(legacy_dir, policy_id), legacy(valuation), max(policy_value, Decimal(0)))


@functools.cache
def admin_fees(legacy_dir, policy_id):
    """{year: admin fees} of a policy: the tariff's fee on the date of every charge run that was not reversed.

    The fee follows the date of the run: e.g. FX generation 03 takes 6.50 until 2022 and 8.00 from 2023.
    """
    policy, fees = contract(legacy_dir, policy_id), {}
    for run in charge_runs(policy):
        fees.setdefault(day(run["EV_EFFDT"]).year, []).append(num(charges(policy, run["EV_EFFDT"])["CG_ADMFEE"], 2))
    return {year: sum(amounts) for year, amounts in fees.items()}


def admin_fee(legacy_dir, policy_id, year):
    """The admin fees of one policy and year, 0 in a year without charge runs."""
    return admin_fees(legacy_dir, policy_id).get(year, Decimal(0))


def rule_outliers(task, predictions, targets):
    """Keys of a task whose target is our own value moved by whole euros."""
    values = {k: v if isinstance(v, tuple) else (v,) for k, v in predictions.items()}
    return {(task, k) for k, target in targets.items() if hand_edited(target, values.get(k))}


def surrender_outliers(legacy_dir, targets):
    """t3 rows whose surrender value is not the target policy value less the penalty.

    Only rows with the diagnostic policy_value column can be checked; a t3 file without it gives no t3 flags.
    """
    return {("t3_surrender_value", k) for k, (surrender, *diagnostic) in targets.items() if diagnostic
            if hand_edited([surrender], [guarded(surrender_value, legacy_dir, *k, diagnostic[0])])}


def admin_outliers(legacy_dir, targets):
    """t4 rows whose admin fees are not the sum of the monthly fees of the year."""
    return {("t4_annual_statement", k) for k, row in targets.items()
            if hand_edited([row[ADMIN_FEES]], [guarded(admin_fee, legacy_dir, *k)])}


def t5_outlier_detection(legacy_dir, targets_dir) -> set[tuple[str, object]]:
    """{(task, key)} of the values that were changed by hand.

    `targets_dir` holds the target files (t0 to t4) of the policies to check, in the format of `targets/`. This is
    the only function that may read target files.
    """
    found = [rule_outliers(task, rule(legacy_dir), read_targets(targets_dir, task)) for task, rule in RULES.items()]
    surrender = surrender_outliers(legacy_dir, read_targets(targets_dir, "t3_surrender_value"))
    return set().union(*found, surrender, admin_outliers(legacy_dir, read_targets(targets_dir, "t4_annual_statement")))
