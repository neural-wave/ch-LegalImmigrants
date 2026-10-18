"""06_calendar.png: t1 due dates vs collection dates for the year after the extract date, as two calendar strips.

Each cell is a day (columns are weeks, rows are weekdays); its colour is the number of premiums due (top) or collected
(bottom) that day, for every policy in force (our t1 output). Ticino public holidays come from
neuron/calendar/holidays.py. Direct debits move to the next business day; bank transfers keep their date.
"""
import datetime as dt

import matplotlib.colors as mcolors
import numpy as np

import style
from style import plt

DAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def grid(counts, first, last):
    """7 x weeks array of counts per day (NaN outside the window), weeks starting on the Monday before `first`."""
    monday = first - dt.timedelta(days=first.weekday())
    weeks = (last - monday).days // 7 + 1
    cells = np.full((7, weeks), np.nan)
    d = first
    while d <= last:
        cells[d.weekday(), (d - monday).days // 7] = counts.get(d.isoformat(), 0)
        d += dt.timedelta(days=1)
    return cells, monday


def draw(numbers):
    c = numbers["calendar"]
    extract = dt.date.fromisoformat(c["extract"])
    first, last = extract + dt.timedelta(days=1), dt.date(extract.year + 1, extract.month, extract.day)
    due, monday = grid(c["due"], first, last)
    collected, _ = grid(c["collected"], first, last)
    holidays = [dt.date.fromisoformat(h) for h in c["holidays"]]
    fig = style.canvas()
    style.heading(fig, "Due on a holiday? The direct debit waits for the next business day",
                  f"Premiums due and collected per day, {first:%B %Y} to {last:%B %Y} (t1, all "
                  f"{c['rows']:,} upcoming payments).",
                  "Holidays of canton Ticino, computed from rules (fixed dates + Easter): neuron/calendar/. "
                  "Bank transfers keep their due date, even on a Sunday.")
    norm = mcolors.PowerNorm(0.45, vmin=0, vmax=np.nanmax(due))
    cmap = mcolors.LinearSegmentedColormap.from_list("blues", [style.LIGHT, style.BLUE_LIGHT, style.BLUE, "#123a6b"])
    cmap.set_bad(style.SURFACE)
    axes = []
    for bottom, cells, title in ((0.5, due, "Premiums\ndue"), (0.115, collected, "Premiums\ncollected")):
        ax = fig.add_axes([0.2, bottom, 0.77, 0.255])
        strip(ax, cells, monday, holidays, norm, cmap)
        fig.text(0.04, bottom + 0.1275, title, fontsize=18, fontweight="bold", va="center")
        axes.append(ax)
    months(axes[0], monday, first, last)
    example(fig, axes[1], c, holidays, monday)
    legend = [plt.Rectangle((0, 0), 1, 1, facecolor=style.SURFACE, edgecolor=style.ORANGE, linewidth=3),
              plt.Rectangle((0, 0), 1, 1, color=style.BLUE)]
    fig.legend(legend, ["Ticino public holiday", "darker = more premiums that day"], loc="lower right",
               bbox_to_anchor=(0.965, 0.04), ncol=2, fontsize=14)
    return style.save_png(fig, "06_calendar")


def strip(ax, cells, monday, holidays, norm, cmap):
    """One calendar strip with weekday labels and holiday outlines."""
    ax.imshow(cells, aspect="auto", cmap=cmap, norm=norm, interpolation="nearest")
    weeks = cells.shape[1]
    ax.set_xticks(np.arange(-0.5, weeks), minor=True)
    ax.set_yticks(np.arange(-0.5, 7), minor=True)
    ax.grid(which="minor", color=style.SURFACE, linewidth=2)
    ax.grid(which="major", visible=False)
    ax.tick_params(which="both", length=0)
    ax.set_xticks([])
    ax.set_yticks(range(7), DAYS, fontsize=13)
    for spine in ax.spines.values():
        spine.set_visible(False)
    for h in holidays:
        col = (h - monday).days // 7
        ax.add_patch(plt.Rectangle((col - 0.5, h.weekday() - 0.5), 1, 1, fill=False, edgecolor=style.ORANGE,
                                   linewidth=2.6))
    ax.axhline(4.5, color=style.INK_2, linewidth=1.2)  # weekend below this line


def months(ax, monday, first, last):
    """Month names above the first week of each month."""
    d = first
    while d <= last:
        ax.text((d - monday).days // 7, -0.9, d.strftime("%b"), fontsize=14, color=style.INK_2, va="bottom")
        d = dt.date(d.year + d.month // 12, d.month % 12 + 1, 1)


def example(fig, ax, c, holidays, monday):
    """The weekday holiday with the most premiums due, spelled out, with an arrow to where its debits go."""
    h = max((h for h in holidays if h.weekday() < 5), key=lambda d: c["due"].get(d.isoformat(), 0))
    nxt = dt.date.fromisoformat(c["next_business_day"][h.isoformat()])
    due, kept = c["due"].get(h.isoformat(), 0), c["collected"].get(h.isoformat(), 0)
    fig.text(0.04, 0.435, f"Example: {c['holidays'][h.isoformat()]}, {h:%a %-d %b %Y}: {due:,} premiums due, only "
             f"{kept:,} collected that day (bank transfers).", fontsize=15, color=style.INK)
    fig.text(0.04, 0.395, f"The direct debits move to {nxt:%a %-d %b} (arrow). Over the year, {c['moved']:,} of "
             f"{c['rows']:,} payments are collected later than due.", fontsize=15, color=style.INK)
    start = ((h - monday).days // 7, h.weekday())
    end = ((nxt - monday).days // 7, nxt.weekday())
    ax.annotate("", end, xytext=start, arrowprops={"arrowstyle": "-|>", "color": style.INK, "lw": 2.2,
                                                   "connectionstyle": "arc3,rad=-0.5", "shrinkA": 6, "shrinkB": 6})
