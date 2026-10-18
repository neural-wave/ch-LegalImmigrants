"""Submission readiness check for any solution folder: the same checks for every solution.

Checks: the official scores on train, runtime and memory, other extract and valuation dates, accounting
invariants, and incomplete exports (one row removed from a table the tasks read, chosen with a fixed seed).
Prints a one-line summary and writes every check's result to tests/out/readiness_<name>.txt.

Usage (Python 3.10+, standard library only):
    python tests/readiness.py <solution folder> <participants folder> [name]
The participants folder is the unzipped challenge folder with legacy/, targets/ and starter_kit/scoring.py.
"""
import csv
import json
import pathlib
import random
import subprocess
import sys
import tempfile

OUT = pathlib.Path(__file__).resolve().parent / "out"
PARTICIPANTS = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else ".").resolve()
KIT = PARTICIPANTS / "starter_kit"
LEGACY, TARGETS = PARTICIPANTS / "legacy", PARTICIPANTS / "targets"
BUDGET_SECONDS, BUDGET_GB = 120, 4

RUNNER = r"""
import json, resource, sys, time, datetime as dt
from decimal import Decimal
sys.path[:0] = [sys.argv[1], sys.argv[2]]
import scoring, submission
legacy, targets, extract, dates = sys.argv[3], sys.argv[4], dt.date.fromisoformat(sys.argv[5]), json.loads(sys.argv[6])
dates = [dt.date.fromisoformat(d) for d in dates]
calls = {
    "t0_commission": lambda: submission.t0_commission(legacy),
    "t1_next_due_dates": lambda: submission.t1_next_due_dates(legacy, extract),
    "t2_projected_maturity_value": lambda: submission.t2_projected_maturity_value(legacy),
    "t3_surrender_value": lambda: submission.t3_surrender_value(legacy, dates),
    "t4_annual_statement": lambda: submission.t4_annual_statement(legacy),
    "t5_outlier_detection": lambda: submission.t5_outlier_detection(legacy, targets),
}
out, started = {}, time.time()
for name, call in calls.items():
    try:
        result = call()
        out[name] = {"ok": True, "rows": len(result)}
        if name != "t5_outlier_detection":
            out[name]["data"] = scoring.normalize(name, result) if name in scoring.TASKS else {}
    except Exception as error:
        out[name] = {"ok": False, "error": type(error).__name__}
out["_seconds"] = time.time() - started
out["_gb"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e9
import pickle; sys.stdout.buffer.write(pickle.dumps(out))
"""


def run(solution, legacy, extract="2026-06-30", dates=("2006-12-31", "2020-04-30", "2025-12-31")):
    """Run every task of `solution` on `legacy` in a fresh process; returns {task: {...}}."""
    import pickle
    cmd = [sys.executable, "-c", RUNNER, str(KIT), str(solution), str(legacy), str(TARGETS), extract, json.dumps(list(dates))]
    proc = subprocess.run(cmd, capture_output=True)
    return pickle.loads(proc.stdout) if proc.returncode == 0 and proc.stdout else {"_crash": proc.stderr.decode()[-300:]}


def rows(table):
    with open(LEGACY / f"{table}.csv", encoding="utf-8") as f:
        return list(csv.reader(f, delimiter=";"))


def without_row(folder, table, index):
    """Link the export into `folder`, writing `table` without its data row number `index`."""
    for path in LEGACY.glob("*.csv"):
        (folder / path.name).symlink_to(path)
    (folder / f"{table}.csv").unlink()
    data = rows(table)
    with open(folder / f"{table}.csv", "w", encoding="utf-8", newline="") as f:
        csv.writer(f, delimiter=";", lineterminator="\n").writerows(r for i, r in enumerate(data) if i != index)


def incomplete_scenarios(seed=2026, per_table=2):
    """(table, row index) pairs: random rows of the tables the tasks read, the same for every solution."""
    rng = random.Random(seed)
    tables = ["NRBROK", "NRPERS", "NRRISK", "NRALLO", "NRPREM", "NRFPRC", "NRFXRT", "NRAGRE", "NRPOLH"]
    return [(t, rng.randrange(1, len(rows(t)))) for t in tables for _ in range(per_table)]


def invariants(result):
    """Accounting checks on the outputs: no negative values, statement totals add up, t1 dates in order."""
    problems = []
    t3 = result.get("t3_surrender_value", {}).get("data", {})
    problems += [f"t3 negative {k}" for k, v in t3.items() if v < 0][:3]
    t4 = result.get("t4_annual_statement", {}).get("data", {})
    problems += [f"t4 total {k}" for k, v in t4.items() if v[5] != sum(v[1:5])][:3]
    t1 = result.get("t1_next_due_dates", {}).get("data", {})
    problems += [f"t1 collection before due {k}" for k, (due, col) in t1.items() if col < due][:3]
    return problems


def main():
    solution = pathlib.Path(sys.argv[1]).resolve()
    name = sys.argv[3] if len(sys.argv) > 3 else solution.name
    import scoring  # noqa: E402  (from the starter kit)
    checks = []

    base = run(solution, LEGACY)
    crashed = [t for t, v in base.items() if isinstance(v, dict) and not v.get("ok", True)]
    checks.append(("all tasks run on the real export", not crashed and "_crash" not in base, crashed))
    for task in scoring.TASKS:
        targets = scoring.read_targets(TARGETS, task)
        mine = base.get(task, {}).get("data", {})
        correct, total = scoring.accuracy(task, mine, targets) if mine else (0, len(targets))
        checks.append((f"{task} scores on train", correct / total > 0.99, f"{correct}/{total}"))
    checks.append((f"runtime under {BUDGET_SECONDS} s", base.get("_seconds", 1e9) < BUDGET_SECONDS, f"{base.get('_seconds', 0):.0f} s"))
    checks.append((f"memory under {BUDGET_GB} GB", base.get("_gb", 1e9) < BUDGET_GB, f"{base.get('_gb', 0):.2f} GB"))
    found = invariants(base)
    checks.append(("accounting invariants hold", not found, found))

    other = run(solution, LEGACY, extract="2027-06-30", dates=("2015-06-30", "2023-12-31"))
    bad = [t for t, v in other.items() if isinstance(v, dict) and not v.get("ok", True)]
    checks.append(("runs with another extract and other valuation dates", not bad and "_crash" not in other, bad))
    t1 = other.get("t1_next_due_dates", {}).get("data", {})
    outside = [k for k, (due, _) in t1.items() if not ("2027-06-30" < due.isoformat() <= "2028-06-30")][:3]
    checks.append(("t1 dates inside the window of that extract date", bool(t1) and not outside, outside))

    for table, index in incomplete_scenarios():
        with tempfile.TemporaryDirectory() as tmp:
            without_row(pathlib.Path(tmp), table, index)
            result = run(solution, tmp)
        failed = [t for t, v in result.items() if isinstance(v, dict) and not v.get("ok", True)]
        checks.append((f"survives {table} missing data row {index}", not failed and "_crash" not in result, failed))

    passed = sum(ok for _, ok, _ in checks)
    report = OUT / f"readiness_{name}.txt"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(f"{'PASS' if ok else 'FAIL'}  {label}  {detail or ''}" for label, ok, detail in checks) + "\n")
    print(f"{name}: readiness {passed}/{len(checks)} checks passed (details: {report})")


if __name__ == "__main__":
    sys.path[:0] = [str(KIT)]
    main()
