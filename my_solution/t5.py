"""t5: manual corrections in the target files of the policies to check.

Three sources, united into one set of (task, key):

- rule residuals: rows where the rule result of a task differs from the target. Only tasks whose
  rules match >= MIN_MATCH of the rows are used (otherwise the residuals are mostly missing rules),
  and a residual counts only if the difference is a whole number of francs (hand corrections are
  round) or the policy is listed in NREXCP;
- shape checks that need no rules (see t5_shape): a t3 surrender value that is not policy value
  x a scale factor to the cent, and a t4 admin fee that is higher than its equal neighbouring
  years and rare in the whole file;
- NREXCP: a listed policy whose key could not be located this way falls back to any residual of
  the policy, for t4 to the rarest admin fee of the policy, and for t2 (single key) to the policy
  itself. Nothing is guessed beyond that: listing every key of a policy would cost more precision
  than it buys recall.

Entry point: solve(legacy_dir, targets_dir, rules), called from submission.py with the rule functions.
"""
from collections import defaultdict
from decimal import Decimal
from itertools import islice

from loader import table
from t5_shape import KEY_TYPES, T2, T3, T4, odd_admin_fees, odd_surrender_values, policy_of, read_target

MIN_MATCH = Decimal("0.97")  # rules below this match rate contribute no residuals


# the scored value columns of a target row as a tuple of Decimal: the columns after the key
# columns, and for t3 only the first of them (policy_value is diagnostic, not scored)
def target_values(task, row):
    values = islice(row.values(), len(KEY_TYPES[task]), None)
    return tuple(Decimal(v) for v in islice(values, 1 if task == T3 else None))


# a prediction (scalar or tuple) as a tuple of Decimal, comparable with target_values
def as_tuple(value):
    return tuple(Decimal(str(v)) for v in (value if isinstance(value, (tuple, list)) else (value,)))


# {task: {policy}} of the manual corrections known in NREXCP (EX_TARGET = "<task>.<column>")
def listed(legacy_dir):
    out = defaultdict(set)
    for row in table(legacy_dir, "NREXCP"):
        out[row["EX_TARGET"].split(".")[0]].add(row["EX_POLNR"])
    return out


# the rule predictions of a task, {} for tasks without rules; t3 rules take the surrender dates
def predictions(task, rules, legacy_dir, targets):
    args = (sorted({d for _, d in targets}),) if task == T3 else ()
    return rules[task](legacy_dir, *args) if task in rules else {}


# {key: diff} of the rows where rule != target (diff = largest column difference, 0 if the shapes
# differ), or {} if the rules are weak: residuals of weak rules are mostly missing rules
def residuals(task, predicted, targets):
    out = {}
    for key, row in targets.items():
        expected, ours = target_values(task, row), as_tuple(predicted.get(key, ()))
        if ours != expected:
            out[key] = max(abs(a - b) for a, b in zip(ours, expected)) if len(ours) == len(expected) else Decimal(0)
    return out if predicted and 1 - Decimal(len(out)) / len(targets) >= MIN_MATCH else {}


# (keys found by round residuals, listed residuals and the shape checks, {policy: rarest t4 key})
def candidates(task, targets, diffs, known):
    # a residual counts if it is a whole number of francs or the policy is listed in NREXCP
    found = {k for k, d in diffs.items() if d == d.to_integral_value() or policy_of(k) in known}
    if task == T3:
        found |= odd_surrender_values(targets)
    odd, rarest = odd_admin_fees(targets) if task == T4 else (set(), {})
    return found | odd, rarest


# keys of a listed policy that nothing located: any residual, else the rarest t4 admin fee, else
# (t2 only, where the policy is the whole key) the policy itself
def fallback(task, policy, diffs, rarest):
    keys = [k for k in diffs if policy_of(k) == policy]
    default = [rarest[policy]] if policy in rarest else ([policy] if task == T2 else [])
    return keys or default


# all keys of one task: the candidates plus the fallback keys of listed policies that have none
def task_keys(task, targets, predicted, known):
    diffs = residuals(task, predicted, targets)
    found, rarest = candidates(task, targets, diffs, known)
    # listed policies that occur in the target file but for which nothing was found yet
    for policy in known & ({policy_of(k) for k in targets} - {policy_of(k) for k in found}):
        found.update(fallback(task, policy, diffs, rarest))
    return found


# {(task, key)}; `rules` = {task: callable(legacy_dir, ...) -> predictions} of the submission.
# Tasks without a target file (rows == {}) contribute nothing.
def solve(legacy_dir, targets_dir, rules):
    known = listed(legacy_dir)
    return {(task, key) for task in KEY_TYPES if (rows := read_target(targets_dir, task))
            for key in task_keys(task, rows, predictions(task, rules, legacy_dir, rows), known[task])}
