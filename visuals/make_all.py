"""Regenerate every visual in visuals/out/ and report/interactive.html from our engine and the challenge data.

Usage (from the project root):
    .venv/bin/python visuals/make_all.py            # recalculate all numbers (~2 min), then draw everything
    .venv/bin/python visuals/make_all.py --reuse    # draw from visuals/data/numbers.json (seconds)
    .venv/bin/python visuals/make_all.py --only 01 05
"""
import argparse
import importlib
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import data  # noqa: E402

VISUALS = ["v01_policy_life", "v02_score_climb", "v03_rule_discovery", "v04_system_change",
           "v05_statement_waterfall", "v06_calendar", "v07_architecture", "v08_unseen_proof", "v09_results_card",
           "v10_rules_found", "v11_interactive"]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reuse", action="store_true", help="draw from the saved numbers.json")
    parser.add_argument("--only", nargs="*", default=[], help="visual numbers to draw, e.g. 01 05")
    args = parser.parse_args()
    numbers = data.load(reuse=args.reuse)
    for name in VISUALS:
        if not args.only or name[1:3] in args.only:
            path = importlib.import_module(name).draw(numbers)
            print(f"{path.relative_to(data.ROOT)}  {path.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
