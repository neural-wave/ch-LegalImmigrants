"""09_results_card.png: the scorecard. Five task tiles (estimated accuracy, raw train score below) and four tiles for
code readability, runtime, readiness checks and the outlier task t5. All values from data/numbers.json."""
from decimal import Decimal

import style

TASKS = {"t0": "t0 Commission", "t1": "t1 Due dates", "t2": "t2 Maturity value", "t3": "t3 Surrender value",
         "t4": "t4 Annual statement"}


def pct(correct, rows):
    """6137 / 6153 -> '99.74', 15028 / 15028 -> '100' (rounded to 4 decimals, but never up to 100)."""
    if correct == rows:
        return "100"
    value = min(round(Decimal(100 * correct) / rows, 4), Decimal("99.9999"))
    return f"{value:.4f}".rstrip("0").rstrip(".")


def tile(fig, x, y, w, h, title, big, color, lines, big_size=46):
    """A card with a title, one big value and up to two small lines."""
    style.panel(fig, x, y, w, h, fill=style.LIGHT)
    fig.text(x + w / 2, y + h - 0.045, title, fontsize=15, fontweight="bold", ha="center", va="center")
    fig.text(x + w / 2, y + h * 0.52, big, fontsize=big_size, fontweight="bold", color=color, ha="center",
             va="center")
    fig.text(x + w / 2, y + 0.05, lines, fontsize=13, color=style.INK_2, ha="center", va="center", linespacing=1.3)


def draw(numbers):
    fig = style.canvas()
    style.heading(fig, "Results: every task at 100% (estimated)",
                  "Exact to the cent and to the day. Code, speed and robustness measured on the same run.",
                  "estimated = hand edits left out, as in the official scoring. Train score = all training rows, "
                  "hand edits counted as wrong.")
    w, gap = 0.172, 0.0145
    for i, (task, s) in enumerate(numbers["scores"].items()):
        est, raw = s["all"], s["all"]
        estimated = pct(est["correct_est"], est["rows_est"]) + "%"
        tile(fig, 0.04 + i * (w + gap), 0.45, w, 0.33, TASKS[task[:2]], estimated, style.BLUE,
             f"estimated\ntrain score {pct(raw['correct'], raw['rows'])}%")
    mi = [m for m in numbers["milestones"] if m["series"] == "MI"][-1]["value"]
    runtime = next(c for c in numbers["readiness"]["checks"] if c.startswith("runtime")).split()[-2]
    r, t5 = numbers["readiness"], numbers["t5"]
    others = t5["flagged"] - t5["listed_found"]
    w2 = (0.92 - 3 * gap) / 4
    bottom = (("Code readability", f"{float(mi):.1f}", style.ORANGE, "maintainability index\n(0–100, higher is better)"),
              ("Runtime", f"{runtime} s", style.AQUA, "all six tasks\non a laptop"),
              ("Readiness checks", f"{r['passed']}/{r['total']}", style.AQUA, "scores, speed, memory,\nmissing data"),
              ("t5 Hand edits", str(t5["flagged"]), style.VIOLET,
               f"rows flagged: {t5['listed_found']} on the official\nlist + {others} that look the same"))
    for i, (title, big, color, lines) in enumerate(bottom):
        tile(fig, 0.04 + i * (w2 + gap), 0.09, w2, 0.31, title, big, color, lines)
    return style.save_png(fig, "09_results_card")
