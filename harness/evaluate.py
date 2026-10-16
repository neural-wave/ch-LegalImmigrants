"""Score predictions exactly like scoring.py does and keep every row, matched or not, with its policy features.

    mm = evaluate("t2_projected_maturity_value", predictions, targets_dir)
    mm.accuracy, mm.mismatches, mm.frame

`diff` is predicted minus target in cents (amounts) or days (dates); for multi-column tasks (t4) it is the diff of
the first value column that differs and `diff_col` names it.
"""
import csv
import dataclasses
import datetime as dt
import decimal
import pathlib

import pandas as pd

from harness import features, paths, scoring

ALIASES = {t[:2]: t for t in scoring.TASKS}  # "t2" -> "t2_projected_maturity_value"


def task_name(task):
    return ALIASES.get(task, task)


def columns(task, targets_dir):
    """(key column names, value column names) from the header of the target file."""
    with open(pathlib.Path(targets_dir) / f"{task}.csv", encoding="utf-8") as f:
        header = next(csv.reader(f))
    n = len(scoring.TASKS[task].key)
    return header[:n], header[n:n + len(scoring.TASKS[task].value)]


def difference(predicted, target):
    """Cents or days between two normalized values; None if the prediction is missing."""
    if predicted is None:
        return None
    if isinstance(target, dt.date):
        return (predicted - target).days
    return int(((decimal.Decimal(predicted) - decimal.Decimal(target)) * 100).to_integral_value())


@dataclasses.dataclass
class Mismatches:
    """All scored rows of a task with the match flag, the diff and the joined policy features."""
    task: str
    frame: pd.DataFrame
    extra_keys: int  # predicted keys that are not in the targets
    key_cols: list
    value_cols: list
    excluded: int = 0  # rows of NREXCP manual corrections left out, like the official evaluation does

    @property
    def total(self):
        return len(self.frame)

    @property
    def correct(self):
        return int(self.frame.match.sum())

    @property
    def accuracy(self):
        return self.correct / self.total if self.total else 0.0

    @property
    def mismatches(self):
        return self.frame[~self.frame.match]

    def __repr__(self):
        return (f"Mismatches({self.task}: {self.correct}/{self.total} = {self.accuracy:.4%}, extra={self.extra_keys}, "
                f"excluded={self.excluded})")


def evaluate(task, predictions, targets_dir=paths.TARGETS, legacy_dir=paths.LEGACY, with_features=True,
             exclude_manual=True):
    """Compare predictions with the train targets of `task` (full name or alias t0..t4).

    With `exclude_manual` the rows of policies that NREXCP lists as corrected by hand for this task are not scored,
    which is what the official evaluation does; set it to False to see them (they are the t5 candidates).
    """
    task = task_name(task)
    targets = scoring.read_targets(targets_dir, task)
    excluded = 0
    all_keys = set(targets)
    if exclude_manual:
        manual = features.manual_corrections(task, legacy_dir)
        before = len(targets)
        targets = {k: v for k, v in targets.items() if (k[0] if isinstance(k, tuple) else k) not in manual}
        excluded = before - len(targets)
    predictions = scoring.normalize(task, predictions)
    key_cols, value_cols = columns(task, targets_dir)
    multi = len(value_cols) > 1
    rows = []
    for key, target in targets.items():
        pred = predictions.get(key)
        row = dict(zip(key_cols, key if isinstance(key, tuple) else (key,)))
        tgt_parts = target if multi else (target,)
        pred_parts = pred if (multi and pred is not None) else ((None,) * len(value_cols) if pred is None else (pred,))
        diffs = [difference(p, t) for p, t in zip(pred_parts, tgt_parts)]
        for col, p, t, d in zip(value_cols, pred_parts, tgt_parts, diffs):
            row[f"pred_{col}"], row[f"tgt_{col}"] = p, t
            if multi:
                row[f"diff_{col}"] = d
        bad = [(c, d) for c, d in zip(value_cols, diffs) if d != 0]
        row["diff"] = bad[0][1] if bad else 0
        row["diff_col"] = bad[0][0] if bad else ""
        row["match"] = pred == target
        rows.append(row)
    frame = pd.DataFrame(rows)
    frame["diff"] = frame["diff"].astype("Int64")
    if with_features:
        frame = frame.join(features.policy_features(legacy_dir), on="policy_id")
        frame = features.row_dates(task, legacy_dir, frame)
    extra = len(set(predictions) - all_keys)
    return Mismatches(task, frame, extra, key_cols, value_cols, excluded)


def read_predictions(task, path):
    """A target-shaped CSV (same header as targets/<task>.csv) -> {key: value} for `evaluate`."""
    task = task_name(task)
    return scoring.TASKS[task].read(path)
