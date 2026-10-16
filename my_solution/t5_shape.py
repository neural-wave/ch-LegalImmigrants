"""t5_shape: the target files of the policies to check, and the shape checks that need no rules.

The target files are the only input of t5 that the other tasks never read. This module

- reads a target file into {key: row} in the submission key format (policy number, plus the
  commission year, surrender date or statement year where the task has a second key column);
- flags t3 rows whose surrender value is not policy value x a scale factor (1.00, 0.99, ... 0.90)
  to the cent: the rule engine only ever produces scaled values, so anything else was typed by hand;
- flags t4 rows whose admin fee is higher than its two equal neighbouring years (or than its only
  neighbour) and occurs at most RARE times in the whole file, and remembers per policy the rarest
  such admin fee as the fallback key for policies listed in NREXCP.

Everything here is pure: no legacy tables, no rules, only the target rows. t5.py unites the results
with the rule residuals and the NREXCP listing.
"""
import csv
import datetime as dt
import pathlib
from collections import Counter
from decimal import Decimal
from itertools import groupby
from operator import itemgetter

# task names as used in the target file names and in NREXCP.EX_TARGET
T0, T2, T3, T4 = "t0_commission", "t2_projected_maturity_value", "t3_surrender_value", "t4_annual_statement"

# converters of the key columns of each target file, in column order
KEY_TYPES = {T0: (str, int), T2: (str,), T3: (str, dt.date.fromisoformat), T4: (str, int)}
SCALES = [Decimal(100 - i) / 100 for i in range(11)]  # surrender value = policy value x scale
CENT = Decimal("0.01")  # tolerance of the scale check
RARE = 2  # an admin fee amount seen at most this often in the file is suspicious


# the submission key of a target row: the bare policy number, or a tuple if there are two key columns
def target_key(task, row):
    parts = tuple(convert(v) for convert, v in zip(KEY_TYPES[task], row.values()))
    return parts[0] if len(parts) == 1 else parts


# the policy number of a submission key (bare policy or (policy, second key))
def policy_of(key):
    return key if isinstance(key, str) else key[0]


# {key: row} of a target file in the submission key format, or {} if the file is missing
def read_target(targets_dir, task):
    path = pathlib.Path(targets_dir) / f"{task}.csv"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8", newline="") as f:
        return {target_key(task, row): row for row in csv.DictReader(f)}


# t3 keys whose surrender value is not policy value x scale: the hand went in between.
# A difference below one franc is rounding, not a correction, and is never flagged.
def odd_surrender_values(targets):
    out = set()
    for key, row in targets.items():
        if "policy_value" not in row:
            break  # target format without the diagnostic column: nothing to check
        value, policy_value = Decimal(row["surrender_value"]), Decimal(row["policy_value"])
        # flagged unless some scale factor reproduces the value to the cent
        if abs(policy_value - value) >= 1 and not any(abs(policy_value * s - value) <= CENT for s in SCALES):
            out.add(key)
    return out


# (t4 keys whose admin fee is a rare amount above its equal neighbouring years, {policy: rarest key}).
# The rarest key of a policy is its first statement year (ascending) whose admin fee amount has the
# lowest count in the file, considering only amounts seen at most RARE times.
def odd_admin_fees(targets):
    fee = {key: Decimal(row["admin_fees"]) for key, row in targets.items()}
    count = Counter(fee.values())
    odd, rarest = set(), {}
    # the keys sort by policy and then by statement year, so each group is one policy's history
    for policy, keys in groupby(sorted(fee), key=itemgetter(0)):
        years = [year for _, year in keys]
        for i, year in enumerate(years):
            amount = fee[(policy, year)]
            if count[amount] > RARE:
                continue  # a common amount is never suspicious
            # the fees of the previous and next statement year (only one of them at the ends)
            neighbours = {fee[(policy, years[j])] for j in (i - 1, i + 1) if 0 <= j < len(years)}
            if len(neighbours) == 1 and amount > neighbours.pop():
                odd.add((policy, year))
            # keep the rarest amount of the policy; ties go to the earliest year
            if count[amount] < rarest.get(policy, (RARE + 1,))[0]:
                rarest[policy] = (count[amount], (policy, year))
    return odd, {policy: key for policy, (_, key) in rarest.items()}
