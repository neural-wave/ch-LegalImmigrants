"""05_statement_waterfall.png: the t4 annual statement of BL10000013 for 2021 as a waterfall.

Premiums paid in the year, minus the four charges the engine calculated from the replayed bookings: entry charge
(taken from each premium), admin fee, management fee and risk charge (monthly, by selling units).
"""
import style

FLOOR = 2000  # euros: the charges are too small to see on an axis from 0
STEPS = (("entry", "Entry charge", "taken from each\npremium"), ("admin", "Admin fee", "fixed, every month"),
         ("management", "Management fee", "share of the\nfund value"),
         ("risk", "Risk charge", "cost of the\nlife cover"))


def draw(numbers):
    s = numbers["policy"]["statement"]
    amounts = {k: float(v) for k, v in s.items() if k != "year"}
    fig = style.canvas()
    style.heading(fig, f"Where a year of premiums goes: the {s['year']} statement",
                  f"Policy {numbers['policy']['policy']}, annual statement (t4). Every charge calculated by our engine, "
                  "exact to the cent.",
                  "Premiums count in the year the money arrived; charges in the year their units were sold "
                  "(tasks/t4_annual_statement.py).")
    ax = fig.add_axes([0.1, 0.25, 0.86, 0.56])
    level, x = amounts["premiums"], 0
    monthly = float(numbers["policy"]["monthly_premium"])
    bar(ax, x, 0, level, style.BLUE, f"€{level:,.2f}", "Premiums paid",
        f"{level / monthly:.0f} monthly premiums\nof €{monthly:.0f} (then a holiday)")
    for key, name, note in STEPS:
        x += 1
        value = amounts[key]
        bar(ax, x, level - value, value, style.ORANGE, f"−€{value:,.2f}", name, note)
        ax.plot([x - 1 + 0.32, x - 0.32], [level, level], color=style.MUTED, linewidth=1.2)
        level -= value
    x += 1
    ax.plot([x - 1 + 0.32, x - 0.32], [level, level], color=style.MUTED, linewidth=1.2)
    bar(ax, x, 0, level, style.AQUA, f"€{level:,.2f}", "After charges", "before fund gains\nor losses")
    top = amounts["premiums"]
    ax.plot([0.32, 5.62], [top, top], color=style.MUTED, linewidth=1, linestyle=":")
    ax.annotate("", (5.55, top - amounts["total"]), xytext=(5.55, top),
                arrowprops={"arrowstyle": "<->", "color": style.INK, "lw": 1.8})
    ax.text(5.65, top - amounts["total"] / 2, f"Total\ncharges\n€{amounts['total']:,.2f}\n"
            f"({amounts['total'] / top:.1%})", fontsize=17, fontweight="bold", va="center")
    ax.set_xlim(-0.5, 6.4)
    ax.set_ylim(FLOOR, top + 160)
    ax.set_ylabel(f"Euros (axis starts at €{FLOOR:,})")
    for x in (0, 5):  # the two full bars are cut by the axis: mark the break
        ax.text(x, FLOOR + 60, "≈", fontsize=34, color=style.SURFACE, ha="center", va="center", fontweight="bold")
    ax.set_xticks([])
    ax.grid(axis="x", visible=False)
    ax.yaxis.set_major_formatter(lambda v, _: f"€{v:,.0f}")
    return style.save_png(fig, "05_statement_waterfall")


def bar(ax, x, bottom, height, color, value, name, note):
    """One waterfall step with its amount above and its name and a short note below the axis."""
    ax.bar(x, height, bottom=bottom, width=0.64, color=color)
    ax.text(x, bottom + height + 12, value, ha="center", va="bottom", fontsize=18, fontweight="bold")
    ax.text(x, -0.04, name, ha="center", va="top", fontsize=15, fontweight="bold", transform=ax.get_xaxis_transform())
    ax.text(x, -0.17, note, ha="center", va="top", fontsize=13, color=style.INK_2, transform=ax.get_xaxis_transform())

