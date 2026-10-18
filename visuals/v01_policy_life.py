"""01_policy_life.gif: the life of policy BL10000013, month by month, from our replay of its bookings.

Stacked area: the value of each fund at the month end (units x price, our engine). Dashed line: premiums paid so far.
Right: what happened in the month (premium in, units bought, the three monthly charges, units sold for them).
"""
import datetime as dt

import matplotlib.dates as mdates

import style
from style import plt

ASSET = {"BD": "bonds", "MX": "mixed", "EQ": "shares", "MM": "money market"}
COLORS = [style.BLUE, style.ORANGE, style.AQUA, style.VIOLET]
MONTHS_PER_FRAME = 2  # the time-lapse speed; it stops and holds on the moments that matter


def month_date(text):
    """'2020-04' -> the month's last day (where the value is measured)."""
    y, m = map(int, text.split("-"))
    return dt.date(y + m // 12, m % 12 + 1, 1) - dt.timedelta(days=1)


def frame_plan(months, surrender, holiday_end):
    """[(month index,)] per frame: two months per frame, holding still on the end of the premium holiday,
    each surrender value and the last month."""
    stops = {s["date"][:7] for s in surrender} | {holiday_end[:7]}
    plan = []
    for i, m in enumerate(months):
        if m["month"] in stops or i == len(months) - 1:
            plan += [(i,)] * (style.LAST if i == len(months) - 1 else style.HOLD)
        elif i % MONTHS_PER_FRAME == 0:
            plan.append((i,))
    return plan


def draw(numbers):
    p = numbers["policy"]
    months, funds = p["months"], list(p["funds"])
    dates = [month_date(m["month"]) for m in months]
    values = {f: [float(m[f]) for m in months] for f in funds}
    paid = [float(m["paid"]) for m in months]
    holiday = [dt.date.fromisoformat(d) for d in p["holiday"]]
    switches = [(dt.date.fromisoformat(s["date"]), s) for s in p["switches"]]
    surrender = {s["date"][:7]: s for s in p["surrender"]}
    fig = style.canvas()
    style.heading(fig, "One policy's life, rebuilt from its bookings",
                  f"Policy {p['policy']}: €{float(p['monthly_premium']):.0f} a month from August 2016. "
                  "Premiums buy fund units; monthly charges sell a few back.",
                  "Calculated by our engine (neuron/funds) from the raw bookings; Neuron's export leaves "
                  "these amounts blank. Surrender values match the targets to the cent.")
    ax = fig.add_axes([0.075, 0.11, 0.6, 0.69])
    side = fig.add_axes([0.71, 0.11, 0.27, 0.69])
    labels = [f"Fund {f} ({ASSET.get(p['funds'][f], p['funds'][f])})" for f in funds]

    def update(i):
        ax.clear()
        ax.set_xlim(dates[0], dt.date(2026, 3, 31))
        ax.set_ylim(0, 35000)
        ax.yaxis.set_major_formatter(lambda v, _: f"€{v / 1000:.0f}k")
        ax.xaxis.set_major_locator(mdates.YearLocator(2))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.set_ylabel("Value at the month end")
        if dates[i] >= holiday[0]:
            ax.axvspan(holiday[0], min(holiday[1], dates[i]), color=style.LIGHT, zorder=0)
            ax.text(holiday[0], 26500, " Premium\n holiday:\n no payments", fontsize=13, color=style.INK_2, va="top")
        ax.stackplot(dates[:i + 1], *[values[f][:i + 1] for f in funds], colors=COLORS, labels=labels,
                     edgecolor=style.SURFACE, linewidth=0.6)
        ax.plot(dates[:i + 1], paid[:i + 1], color=style.INK_2, linestyle="--", linewidth=2, label="Premiums paid so far")
        ax.legend(loc="upper left", fontsize=13)
        shown = [(d, paid[dates.index(month_date(d.isoformat()[:7]))]) for d, _ in switches if d <= dates[i]]
        for d, y in shown:
            ax.plot(d, y + 900, "v", markersize=10, color=style.INK_2)
        if shown:
            ax.text(shown[0][0], shown[-1][1] + 2200, f"fund switch{'es' if len(shown) > 1 else ''}",
                    fontsize=12, color=style.INK_2, ha="left")
        for month, s in surrender.items():
            j = next(n for n, m in enumerate(months) if m["month"] == month)
            if j <= i:
                v = float(s["surrender"])
                ax.plot(dates[j], v, "o", markersize=12, color=style.INK, markeredgecolor=style.SURFACE, zorder=5)
                when = month_date(month).strftime("%-d %b %Y")
                ax.annotate(f"If surrendered on {when}:\n{style.euros(v, 2)}", (dates[j], v),
                            xytext=(-205, 22) if j == len(months) - 1 else (-190, 70), textcoords="offset points",
                            fontsize=15, fontweight="bold", color=style.INK, ha="left",
                            arrowprops={"arrowstyle": "-", "color": style.INK})
        ledger(side, months[i])

    plan = frame_plan(months, p["surrender"], p["holiday"][1])
    return style.save_gif(fig, "01_policy_life", update, plan, still=plan[-1])


def ledger(ax, m):
    """The month's bookings as a small statement."""
    ax.clear()
    ax.axis("off")
    ax.add_patch(plt.Rectangle((0, 0), 1, 1, color=style.LIGHT, transform=ax.transAxes, zorder=0))
    when = dt.date.fromisoformat(m["month"] + "-01").strftime("%B %Y")
    ax.text(0.07, 0.92, when, fontsize=22, fontweight="bold", transform=ax.transAxes)
    premium = float(m["premium"])
    rows = [("Premium paid", style.euros(premium, 2) if premium else "none (holiday)", style.INK),
            ("  buys fund units", f"+{float(m['units_bought']):.2f}", style.BLUE),
            ("Admin fee", f"−{style.euros(float(m['ADM']), 2)}", style.INK),
            ("Management fee", f"−{style.euros(float(m['AMC']), 2)}", style.INK),
            ("Risk (life cover)", f"−{style.euros(float(m['RSK']), 2)}", style.INK),
            ("  sells fund units", f"−{float(m['units_cancelled']):.2f}", style.ORANGE)]
    for n, (label, value, color) in enumerate(rows):
        y = 0.79 - n * 0.085
        ax.text(0.07, y, label, fontsize=15, color=style.INK_2, transform=ax.transAxes)
        ax.text(0.93, y, value, fontsize=15, color=color, ha="right", transform=ax.transAxes, fontweight="bold")
    ax.plot([0.07, 0.93], [0.27, 0.27], color=style.AXIS, transform=ax.transAxes, linewidth=1)
    ax.text(0.07, 0.17, "Fund value", fontsize=16, color=style.INK_2, transform=ax.transAxes)
    ax.text(0.93, 0.17, style.euros(float(m["value"]), 2), fontsize=19, fontweight="bold", ha="right",
            transform=ax.transAxes)
    ax.text(0.07, 0.07, "Paid so far", fontsize=16, color=style.INK_2, transform=ax.transAxes)
    ax.text(0.93, 0.07, style.euros(float(m["paid"]), 2), fontsize=16, ha="right", color=style.INK_2,
            transform=ax.transAxes)
