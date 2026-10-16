"""Greedy coordinate search over named rule variants.

    space = {"rounding": ["era", "half_up", "truncate"], "monthly_rate": ["r_over_12", "geometric"]}
    result = search("t2", build_fn, space)        # build_fn(config: dict) -> predictions
    result.best, result.accuracy, result.trials

Configs are plain dicts {dimension: variant}; a new idea (from a person or an LLM) is one more entry in `space`.
One dimension changes at a time, an improvement is kept at once, and the sweep repeats until a full round brings
nothing. Every trial is logged with its exact accuracy.
"""
import dataclasses
import time

from harness import paths
from harness.evaluate import evaluate, task_name


@dataclasses.dataclass
class SearchResult:
    best: dict
    accuracy: float
    correct: int
    total: int
    trials: list  # [{"config", "correct", "total", "accuracy", "seconds", "kept"}]

    def log(self):
        for i, t in enumerate(self.trials, 1):
            mark = "*" if t["kept"] else " "
            print(f"{mark} {i:3d} {t['correct']:7d}/{t['total']:<7d} {t['accuracy']:8.4%} {t['seconds']:6.1f}s {t['config']}")


def search(task, build_fn, space, targets_dir=paths.TARGETS, start=None, max_rounds=5, verbose=True):
    """Return the best config found by one-dimension-at-a-time hill climbing from `start` (default: first variants)."""
    task = task_name(task)
    current = dict(start or {k: list(v)[0] for k, v in space.items()})
    seen, trials = {}, []

    def score(config):
        key = tuple(sorted(config.items()))
        if key in seen:
            return seen[key]
        started = time.time()
        mm = evaluate(task, build_fn(dict(config)), targets_dir, with_features=False)
        trial = {"config": dict(config), "correct": mm.correct, "total": mm.total, "accuracy": mm.accuracy,
                 "seconds": time.time() - started, "kept": False}
        trials.append(trial)
        seen[key] = trial
        if verbose:
            print(f"  {mm.correct}/{mm.total} = {mm.accuracy:.4%}  {config}")
        return trial

    best = score(current)
    best["kept"] = True
    for _ in range(max_rounds):
        improved = False
        for dim, variants in space.items():
            for variant in variants:
                if variant == current[dim]:
                    continue
                trial = score({**current, dim: variant})
                if trial["correct"] > best["correct"]:
                    best, current, improved = trial, dict(trial["config"]), True
                    trial["kept"] = True
                    if verbose:
                        print(f"  -> keep {dim} = {variant!r}")
        if not improved:
            break
    return SearchResult(current, best["accuracy"], best["correct"], best["total"], trials)
