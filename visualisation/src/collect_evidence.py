"""Re-run t2 rounding counterfactuals; retain aggregate statistics only.

The policy age convention and all rates stay unchanged. Only the rounding helper
is temporarily replaced, inside this process. Submission source is never edited.
Historical sample scores are read from the DataAnalytics Git branch.
"""
from collections import defaultdict
from decimal import ROUND_DOWN, ROUND_HALF_UP
import argparse
import csv
import importlib
import json
from pathlib import Path
import subprocess
import sys
from datetime import date

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--legacy", type=Path, default=ROOT / "LifewareChallenge/participants/legacy")
    parser.add_argument("--targets", type=Path, default=ROOT / "LifewareChallenge/participants/targets")
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT / "my_solution"))
    from neuron.contract import contract, conversion_date
    from neuron.data import day
    from decimal import Decimal
    rounding_module = importlib.import_module("neuron.contract")
    task = importlib.import_module("tasks.t2_projected_maturity_value")
    with (args.targets / "t2_projected_maturity_value.csv").open() as stream:
        reader = csv.reader(stream)
        next(reader)
        targets = {r[0]: Decimal(r[1]) for r in reader}
    legacy = str(args.legacy.resolve())
    original = rounding_module.rounding
    predictions = {}
    try:
        for label, mode in (("historical", None), ("half_up_everywhere", ROUND_HALF_UP),
                            ("truncate_everywhere", ROUND_DOWN)):
            rounding_module.rounding = original if mode is None else lambda cobol, mode=mode: mode
            predictions[label] = task.t2_projected_maturity_value(legacy)
            print(label, sum(predictions[label].get(k) == v for k, v in targets.items()), len(targets), flush=True)
    finally:
        rounding_module.rounding = original
    cut = day(conversion_date(legacy))
    bins = defaultdict(lambda: {"n": 0, **{k: 0 for k in predictions}})
    era_totals = defaultdict(lambda: {"n": 0, **{k: 0 for k in predictions}})
    for key, expected in targets.items():
        applied = day(contract(legacy, key).first["PH_APPDT"])
        quarter = date(applied.year, ((applied.month - 1) // 3) * 3 + 1, 1).isoformat()
        era = "COBOL offers" if applied < cut else "Java offers"
        for bucket in (bins[quarter], era_totals[era]):
            bucket["n"] += 1
            for variant, rows in predictions.items():
                bucket[variant] += rows.get(key) != expected
    evidence = {
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "conversion": cut.isoformat(), "target_count": len(targets),
        "method": "Only neuron.contract.rounding replaced; age conventions and all parameters unchanged.",
        "interpretation": "Exact-row mismatch against train targets, including manually altered target rows.",
        "quarters": [{"quarter": key, **value} for key, value in sorted(bins.items())],
        "era_totals": dict(era_totals),
    }
    out = ROOT / "visualisation/data"
    out.mkdir(parents=True, exist_ok=True)
    (out / "rounding-evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
    snapshots = []
    for version in (53, 57, 64, 75, 79):
        raw = subprocess.check_output(["git", "show", f"DataAnalytics:DataAnalytics/analysis/local_rescore/s{version}.json"], cwd=ROOT, text=True)
        record = json.loads(raw)
        tasks = record["tasks"]
        snapshots.append({"upload": version,
                          "payout": [sum(tasks[f"t7_tax_payout_sample_{i}"][j] for i in (1, 2)) for j in (0, 1)],
                          "annual": [sum(tasks[f"t7_tax_annual_sample_{i}"][j] for i in (1, 2)) for j in (0, 1)],
                          "mi": record["mi"]})
    (out / "sample-rescores.json").write_text(json.dumps({
        "source": "DataAnalytics/analysis/local_rescore/sNN.json, stored on DataAnalytics branch",
        "evaluation": "Retrospective released-sample re-score, not leaderboard or independent holdout.",
        "caution": "Final rules were developed using these samples. Do not infer private-set accuracy.",
        "snapshots": snapshots}, indent=2) + "\n")


if __name__ == "__main__":
    main()
