"""Command line of the harness.

    python -m harness.cli evaluate t2 --submission ../my_solution --legacy ../../data/legacy --targets ../../data/targets
    python -m harness.cli evaluate t0 --predictions harness/reports/t0/predictions.csv

Runs the task function of the submission (or reads a target-shaped CSV of predictions), scores it exactly,
prints the explanation and saves report.md + PNGs to harness/reports/<task>/ (or --out).
"""
import argparse
import importlib.util
import sys
import time

from harness import paths, report, scoring
from harness.explain import explain
from harness.evaluate import evaluate, read_predictions, task_name


def load_submission(folder):
    sys.path.insert(0, str(folder))
    spec = importlib.util.spec_from_file_location("submission", f"{folder}/submission.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def predictions_of(args, task):
    if args.predictions:
        return read_predictions(task, args.predictions), f"predictions {args.predictions}"
    submission = load_submission(args.submission)
    targets = scoring.read_targets(args.targets, task)
    started = time.time()
    preds = getattr(submission, task)(str(args.legacy), *scoring.arguments(task, targets))
    print(f"{task} computed in {time.time() - started:.1f}s")
    return preds, f"submission {args.submission}"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("evaluate", help="score, explain and report one task")
    p.add_argument("task", help="t0..t4 or the full task name")
    p.add_argument("--submission", default=paths.SUBMISSION)
    p.add_argument("--predictions", help="target-shaped CSV instead of running the submission")
    p.add_argument("--legacy", default=paths.LEGACY)
    p.add_argument("--targets", default=paths.TARGETS)
    p.add_argument("--out", help="report folder (default harness/reports/<task>)")
    p.add_argument("--top", type=int, default=10)
    p.add_argument("--keep-nrexcp", action="store_true", help="score the NREXCP manual corrections too")
    args = parser.parse_args(argv)
    task = task_name(args.task)
    preds, label = predictions_of(args, task)
    mm = evaluate(task, preds, args.targets, args.legacy, exclude_manual=not args.keep_nrexcp)
    findings = explain(mm, top=args.top)
    out = report.write_report(mm, findings, args.out, label)
    print(f"\nreport saved to {out}")


if __name__ == "__main__":
    main()
