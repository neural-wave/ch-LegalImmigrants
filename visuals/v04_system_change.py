"""04_system_change.png: the COBOL -> Java change of 11 Aug 2007, seen in the t2 maturity values.

Three versions of our t2 rule run on every training policy: COBOL rules for all offers (cents cut off, ages in
365-day years), Java rules for all (cents rounded half up, ages in whole months), and ours (switch on the conversion
date, event 800). Plotted: the share of offers whose projected maturity value is wrong, by the date they were signed.
"""
import datetime as dt

import matplotlib.dates as mdates

import style

LABELS = {"cobol": (dt.date(2026, 6, 1), 93, "right"), "java": (dt.date(1995, 1, 1), 93, "left"),
          "ours": (dt.date(2026, 6, 1), 7, "right")}  # where each line's label sits: (x, y %, alignment)
RUNS = (("cobol", "Old COBOL rules for every year", style.VIOLET),
        ("java", "New Java rules for every year", style.ORANGE),
        ("ours", "Our rule: switch on 11 Aug 2007", style.BLUE))


def periods(conversion):
    """Calendar years, with 2007 split at the conversion date: [(start, end)]."""
    edges = [dt.date(y, 1, 1) for y in range(1994, 2027)] + [conversion]
    edges = sorted(edges)
    return list(zip(edges, edges[1:] + [dt.date(2027, 1, 1)]))


def error_rates(policies, name, bins):
    """[(start, end, share wrong, count)] per period of the signing date."""
    out = []
    for start, end in bins:
        rows = [p for p in policies if start <= dt.date.fromisoformat(p["signed"]) < end]
        if rows:
            out.append((start, end, 100 * sum(not p[name] for p in rows) / len(rows), len(rows)))
    return out


def draw(numbers):
    era = numbers["era"]
    conversion = dt.date.fromisoformat(era["conversion"])
    bins = periods(conversion)
    fig = style.canvas()
    style.heading(fig, "In 2007 Neuron moved from COBOL to Java, and the maths changed",
                  "Share of offers whose projected value at maturity (t2) is wrong, by the date the offer was signed.",
                  f"Training policies: {len(era['policies']):,} offers. Same rule three times, only the era switch "
                  "changes (our engine, neuron/era.py). Our 8 misses are hand edits.")
    ax = fig.add_axes([0.085, 0.16, 0.88, 0.64])
    ax.axvspan(dt.date(1994, 1, 1), conversion, color=style.LIGHT, zorder=0)
    ax.axvline(conversion, color=style.INK_2, linestyle="--", linewidth=1.5)
    ax.text(conversion, 104, "  11 Aug 2007: COBOL → Java", fontsize=15, color=style.INK, fontweight="bold")
    ax.text(dt.date(1995, 1, 1), 60, "COBOL years:\ncents cut off,\nage in 365-day years", fontsize=14,
            color=style.INK_2, va="top")
    ax.text(dt.date(2015, 1, 1), 60, "Java years:\ncents rounded,\nage in whole months", fontsize=14,
            color=style.INK_2, va="top")
    for name, label, color in RUNS:
        rates = error_rates(era["policies"], name, bins)
        xs = [r[0] for r in rates] + [rates[-1][1]]
        ys = [r[2] for r in rates] + [rates[-1][2]]
        ours = name == "ours"  # thin on top, so the thick era lines stay visible under it
        ax.step(xs, ys, where="post", color=color, linewidth=3 if ours else 9, alpha=1 if ours else 0.8,
                solid_capstyle="butt", zorder=4 if ours else 3)
        wrong = sum(not p[name] for p in era["policies"])
        x, y, align = LABELS[name]
        ax.text(x, y, f"{label} ({wrong:,} wrong)", fontsize=15, color=color, fontweight="bold", ha=align,
                va="center", zorder=5, bbox={"facecolor": style.SURFACE, "edgecolor": "none", "pad": 2, "alpha": 0.9})
    ax.set_ylim(-4, 108)
    ax.set_xlim(dt.date(1994, 1, 1), dt.date(2027, 1, 1))
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    ax.set_ylabel("Offers with a wrong value")
    ax.xaxis.set_major_locator(mdates.YearLocator(5))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_xlabel("Date the offer was signed")
    return style.save_png(fig, "04_system_change")
