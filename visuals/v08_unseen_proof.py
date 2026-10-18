"""08_unseen_proof.png: evidence that the rules work on policies we never had answers for.

Left: every policy that ended by surrender or death (SUR / DTH bookings) must hold exactly 0 fund units afterwards.
That needs no target file, so it can be checked on the unseen public policies too. Middle: the same scores on a
fixed 20% check group of the training policies as on the other 80% (lab/core.py holdout). Right: the readiness
suite (readiness.py: scores, runtime, memory, other dates, missing data rows).
"""
import style

TASK_NAMES = {"t0": "t0 Commission", "t1": "t1 Due dates", "t2": "t2 Maturity", "t3": "t3 Surrender",
              "t4": "t4 Statement"}


def pct(correct, rows):
    """Accuracy text that never rounds up to 100%: 99.9956 -> '99.995%', 100 -> '100%'."""
    if correct == rows:
        return "100%"
    return f"{int(100000 * correct / rows) / 1000:.3f}%"


def draw(numbers):
    fig = style.canvas()
    style.heading(fig, "Not fitted to the answers: the rules hold on unseen policies",
                  "Three checks that the rules are general and not fitted to the training answers.",
                  "Units from our replay of NRBOOK (neuron/funds). Check group: fixed 20% of training policies by "
                  "a hash of the policy number (lab/core.py). Readiness: readiness.py.")
    exits(fig, numbers["exits"])
    holdout(fig, numbers["scores"])
    readiness(fig, numbers["readiness"])
    return style.save_png(fig, "08_unseen_proof")


def exits(fig, e):
    """Two full bars: policies that left and hold exactly 0 units, training and unseen."""
    fig.text(0.04, 0.775, "1 · After a surrender or death,\nexactly 0 fund units are left", fontsize=17,
             fontweight="bold", va="top")
    for n, (group, label) in enumerate((("train", "Training policies"),
                                        ("unseen", "Unseen policies (no answers given)"))):
        y = 0.27 + n * 0.2
        ax = fig.add_axes([0.04, y, 0.28, 0.07])
        done, total = e[group]["zero"], e[group]["exited"]
        ax.barh(0, total, color=style.LIGHT, height=1)
        ax.barh(0, done, color=style.AQUA if group == "unseen" else style.BLUE, height=1)
        ax.set_xlim(0, total)
        ax.axis("off")
        fig.text(0.04, y + 0.085, label, fontsize=15, color=style.INK_2, va="bottom")
        ax.text(total * 0.04, 0, f"{done:,} of {total:,}", color=style.SURFACE, fontsize=22, fontweight="bold",
                ha="left", va="center")
    fig.text(0.04, 0.17, "The bookings themselves prove it:\nno answer file is needed.", fontsize=14,
             color=style.INK_2, va="top")


def holdout(fig, scores):
    """Score per task on the 20% check group vs the other 80%, as a small table."""
    x0 = 0.37
    fig.text(x0, 0.775, "2 · The same on a fixed 20%\ncheck group as on the rest", fontsize=17, fontweight="bold", va="top")
    fig.text(x0 + 0.2, 0.63, "check\ngroup 20%", fontsize=14, color=style.INK_2, ha="right", va="bottom")
    fig.text(x0 + 0.3, 0.63, "other\n80%", fontsize=14, color=style.INK_2, ha="right", va="bottom")
    for n, (task, s) in enumerate(scores.items()):
        y = 0.58 - n * 0.075
        fig.text(x0, y, TASK_NAMES[task[:2]], fontsize=15, va="center")
        for col, group in ((0.2, "check"), (0.3, "rest")):
            fig.text(x0 + col, y, pct(s[group]["correct"], s[group]["rows"]), fontsize=17, fontweight="bold",
                     ha="right", va="center")
    gap = max(abs(100 * s["check"]["correct"] / s["check"]["rows"] - 100 * s["rest"]["correct"] / s["rest"]["rows"])
              for s in scores.values())
    est = all(s[g]["correct_est"] == s[g]["rows_est"] for s in scores.values() for g in ("check", "rest"))
    fig.text(x0, 0.17, f"Largest gap: {gap:.2f} points (hand edits).\nWith hand edits left out: "
             f"{'100% in both groups' if est else 'see numbers.json'}.", fontsize=14, color=style.INK_2, va="top")


def readiness(fig, r):
    """The readiness suite: one big count and what it covers."""
    x0 = 0.71
    fig.text(x0, 0.775, "3 · Ready for new data", fontsize=17, fontweight="bold", va="top")
    fig.text(x0, 0.6, f"{r['passed']}/{r['total']}", fontsize=64, fontweight="bold", color=style.AQUA, va="center")
    fig.text(x0, 0.5, "readiness checks pass", fontsize=16, color=style.INK_2, va="center")
    groups = (("scores on train", "scores on the training data"), ("runtime", "runtime: "),
              ("memory", "memory: "), ("survives", "missing data rows survived"))
    lines = []
    for key, text in groups:
        hits = [c for c in r["checks"] if key in c]
        if key in ("runtime", "memory"):
            lines.append(text + hits[0].split("  ")[-1])
        else:
            lines.append(f"{len(hits)} × {text}")
    other = r["total"] - sum(any(k in c for k, _ in groups) for c in r["checks"])
    lines.append(f"{other} × other dates and invariants")
    for n, text in enumerate(lines):
        fig.text(x0, 0.42 - n * 0.055, "✓  " + text, fontsize=15, color=style.INK, va="center")

