"""Demo of the harness on t2 with the exploration rules of analiza/t2_recon.py.

Builds the predictions of the winning configuration (CFG of t2_recon), caches them as a target-shaped CSV in
harness/reports/t2/predictions.csv, and runs the evaluate -> explain -> report pipeline on them.

    .venv/bin/python -m harness.demo_t2            # from repo/
    .venv/bin/python -m harness.demo_t2 --rebuild  # ignore the cached predictions
"""
import csv
import pathlib
import sys

from harness import cli, paths

ANALIZA = paths.LIFEWARE / "analiza"
CACHE = paths.REPORTS / "t2" / "predictions.csv"


def build_predictions():
    """{policy_id: Decimal} of t2_recon's CFG for every train policy."""
    sys.path.insert(0, str(ANALIZA))
    import t2_recon as t  # noqa: E402  (loads the legacy tables at import)

    targets = t.scoring.read_targets(paths.TARGETS, "t2_projected_maturity_value")
    out = {}
    for policy in sorted(targets):
        try:
            out[policy] = t.r2(t.project(policy, t.CFG)[0])
        except Exception as exc:  # noqa: BLE001  (a failing policy is a mismatch, not a crash)
            print(policy, "ERR", exc)
    return out


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--rebuild" in argv or not CACHE.exists():
        preds = build_predictions()
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        with open(CACHE, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["policy_id", "maturity_value"])
            w.writerows(sorted(preds.items()))
    cli.main(["evaluate", "t2", "--predictions", str(CACHE)])


if __name__ == "__main__":
    main()
