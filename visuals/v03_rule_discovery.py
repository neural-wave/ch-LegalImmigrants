"""03_rule_discovery.gif: how the t0 commission rule was found with the lab tools.

1. The simplest guess (the broker of the policy's current version, lab/variants/t0_commission.py) gets rows wrong.
2. A decision tree (as in lab/miner.py) finds what those rows share: the broker's tier changed during the policy.
3. The fixed rule (the broker of the version valid on the money date, tasks/t0_commission.py) clears them.
4. What is left are isolated hand edits, for the outlier task t5.
"""
import datetime as dt

import matplotlib.dates as mdates
import numpy as np

import style

YMIN, YMAX = -85, 50  # commission error axis (€); rarer, bigger errors are drawn on the edge
STILL = (1, None)  # the settled frame saved as a PNG for the report: step 2, the decision tree


def draw(numbers):
    t0 = numbers["t0"]
    pts = t0["points"]
    x = mdates.date2num([dt.date.fromisoformat(p["date"]) for p in pts])
    y = np.clip([p["delta"] for p in pts], YMIN + 2, YMAX - 2)
    fixed = np.array([p["fixed"] for p in pts])
    fig = style.canvas()
    style.heading(fig, "How a rule is found: who earns the commission?",
                  source="Lab tools: lab/variants/t0_commission.py (simple guess), lab/miner.py (decision tree), "
                         "tasks/t0_commission.py (final rule). Errors beyond the axis are drawn on its edge.")
    heading = fig.text(style.LAYOUT["margin_x"], 0.862, "", fontsize=style.SIZE["step"], color=style.INK_2)
    ax = fig.add_axes([0.1, 0.15, 0.515, 0.67])
    side = fig.add_axes([0.66, 0.13, 0.32, 0.69])

    def update(step, progress):
        """A step is drawn settled (progress None) or moving into it; the heading only names settled steps."""
        t = 1.0 if progress is None else style.ease(progress)
        heading.set_text(STEPS[step if progress is None else step - 1].format(**t0))
        fix = 0.0 if step < 2 else t if step == 2 else 1.0
        wrong = t0["naive_wrong"] + round((t0["shipped_wrong"] - t0["naive_wrong"]) * fix)
        scatter(ax, x, y, fixed, step, fix)
        panel(side, step, t, wrong, t0)

    return style.save_gif(fig, "03_rule_discovery", update, style.steps(len(STEPS)), still=STILL)


STEPS = ["Step 1 of 4 · Simplest guess: the broker the policy has today",
         "Step 2 of 4 · A decision tree looks for what the wrong rows have in common",
         "Step 3 of 4 · New rule: the broker on the day the money arrived",
         "Step 4 of 4 · {shipped_wrong} rows left: hand edits in the old system (outlier task t5)"]


def scatter(ax, x, y, fixed, step, fix):
    """Each wrong row at (money date, commission error); fixed rows slide to 0 and vanish in step 3."""
    ax.clear()
    ax.set_ylim(YMIN, YMAX)
    ax.set_xlim(mdates.date2num(dt.date(1994, 1, 1)), mdates.date2num(dt.date(2026, 12, 31)))
    ax.xaxis.set_major_locator(mdates.YearLocator(5))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.yaxis.set_major_formatter(lambda v, _: f"+€{v:.0f}" if v > 0 else f"−€{-v:.0f}" if v < 0 else "right")
    ax.set_ylabel("Commission error per premium (€)")
    ax.set_xlabel("Date the premium was received")
    ax.axhline(0, color=style.BLUE, linewidth=6, alpha=0.35, zorder=1)
    if fix < 1:
        ax.scatter(x[fixed], y[fixed] * (1 - fix), s=22, color=style.RED, alpha=0.75 * (1 - fix), linewidths=0,
                   zorder=3)
    rest = ~fixed
    ax.scatter(x[rest], y[rest], s=90 if step else 22, color=style.VIOLET if step else style.RED,
               linewidths=1.5 if step else 0, edgecolors=style.SURFACE, zorder=4)
    if step == 3:
        ax.text(0.98, 0.92, "hand edit: a whole-euro change\nthat no rule explains", transform=ax.transAxes,
                ha="right", va="top", fontsize=15, color=style.VIOLET, fontweight="bold")


def panel(ax, step, t, wrong, t0):
    """The count of wrong and right rows and, from step 2, the decision tree's first question."""
    ax.clear()
    ax.axis("off")
    color = style.RED if step < 3 else style.VIOLET
    ax.text(0.5, 0.93, f"{wrong:,}", fontsize=58, fontweight="bold", ha="center", va="center", color=color,
            transform=ax.transAxes)
    exact = 100 * (t0["rows"] - wrong) / t0["rows"]
    ax.text(0.5, 0.79, f"rows wrong of {t0['rows']:,}", fontsize=15, ha="center", color=style.INK_2,
            transform=ax.transAxes)
    ax.text(0.5, 0.735, f"{t0['rows'] - wrong:,} exactly right ({exact:.2f}%)" if wrong > 100 else
            f"{t0['rows'] - wrong:,} exactly right ({exact:.4f}%)", fontsize=15, ha="center", color=style.BLUE,
            transform=ax.transAxes)
    if step >= 1:
        tree(ax, t0, alpha=(t if step == 1 else 0.55))


def tree(ax, t0, alpha):
    """Root question and two leaves, with the counts the tree split gives on all rows (faded after step 2)."""
    box = {"boxstyle": "round,pad=0.6", "facecolor": style.LIGHT, "edgecolor": style.AXIS}
    ax.text(0.5, 0.58, "Did the broker's commission\nlevel change during the policy?", ha="center", va="center",
            fontsize=15, fontweight="bold", bbox=box, transform=ax.transAxes, alpha=alpha)
    for xpos, answer, rows, wrong, color in ((0.23, "Yes", t0["split_yes_rows"], t0["split_yes_wrong"], style.RED),
                                             (0.77, "No", t0["split_no_rows"], t0["split_no_wrong"], style.INK_2)):
        ax.annotate("", (xpos, 0.40), xytext=(0.5, 0.49), xycoords="axes fraction",
                    arrowprops={"arrowstyle": "-|>", "color": style.MUTED, "alpha": alpha, "lw": 1.5})
        ax.text(xpos, 0.30, f"{answer}\n{rows:,} rows\n{wrong:,} wrong", ha="center", va="center", fontsize=15,
                color=color, fontweight="bold", transform=ax.transAxes, alpha=alpha,
                bbox={**box, "facecolor": style.SURFACE})
    share = t0["split_yes_wrong"] / t0["naive_wrong"]
    ax.text(0.5, 0.13, f"{share:.0%} of the wrong rows: the broker changed.\nClue: the date decides which broker counts.",
            ha="center", va="top", fontsize=14, color=style.INK, transform=ax.transAxes, alpha=alpha)
