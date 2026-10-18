"""Our own t7 check (stdlib only): runs t7_tax_payout and t7_tax_annual on the legacy export, reports how many rows
survive the official scoring_t7.normalize, and scores them against tests/t7_examples/, which holds only the two
example rows of the challenge PDF (BL10000086 event 121 and BL10000044 2019). Expected: 2 / 2.

Usage: .venv/bin/python tests/check_t7.py [legacy_dir]
"""
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
KIT = ROOT / "LifewareChallenge/participants/starter_kit"
sys.path[:0] = [str(KIT), str(KIT / "my_solution")]
import scoring_t7  # noqa: E402
import submission  # noqa: E402

legacy = sys.argv[1] if len(sys.argv) > 1 else str(KIT.parent / "legacy")
examples = pathlib.Path(__file__).resolve().parent / "t7_examples"
correct_total = scored_total = 0
for task in ("t7_tax_payout", "t7_tax_annual"):
    started = time.time()
    rows = getattr(submission, task)(legacy)
    survived = len(scoring_t7.normalize(task, rows))
    correct, scored = scoring_t7.accuracy(task, rows, scoring_t7.read_targets(examples, task))
    correct_total, scored_total = correct_total + correct, scored_total + scored
    print(f"{task:14s} rows {len(rows):5d}  survive normalize {survived:5d}  PDF examples {correct}/{scored}  "
          f"{time.time() - started:.0f} s")
print(f"PDF examples total: {correct_total}/{scored_total}")
sys.exit(0 if correct_total == scored_total and scored_total else 1)
