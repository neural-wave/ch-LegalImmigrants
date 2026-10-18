"""Score t7 on the leaderboard samples Lifeware released (participants/t7_samples/sample_*), with the official
scoring_t7, and print every wrong row (ours vs the answer, differing columns marked). Lab tool, not part of the
package.

Usage: .venv/bin/python tests/samples_t7.py [--quiet]
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
KIT = ROOT / "LifewareChallenge/participants/starter_kit"
sys.path[:0] = [str(KIT), str(KIT / "my_solution")]
import scoring_t7  # noqa: E402
import submission  # noqa: E402

LEGACY, SAMPLES = str(KIT.parent / "legacy"), KIT.parent / "t7_samples"
ours = {task: scoring_t7.normalize(task, getattr(submission, task)(LEGACY)) for task in ("t7_tax_payout", "t7_tax_annual")}
for folder in sorted(SAMPLES.glob("sample_*")):
    for task, mine in ours.items():
        targets = scoring_t7.read_targets(folder, task)
        wrong = [k for k in targets if mine.get(k) != targets[k]]
        print(f"{folder.name} {task}: {len(targets) - len(wrong)}/{len(targets)}")
        if "--quiet" in sys.argv:
            continue
        for k in wrong:
            got, want = mine.get(k), targets[k]
            cols = [i for i in range(len(want)) if got is None or got[i] != want[i]]
            print("   ", k, "cols", cols, "\n      ours", got, "\n      want", want)
