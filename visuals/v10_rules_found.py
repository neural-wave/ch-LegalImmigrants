"""10_rules_found.png: eight rules we found, each with one real example from our engine and the data.

Sources: numbers["rules"] (data.rule_examples), the calendar (t1) and the era test (t2); the COBOL management-fee
day count is from logs/t3-t4.md (a policy started on the 31st, run of 29 February: 29 days).
"""
import datetime as dt
import textwrap

import style

COLORS = [style.BLUE, style.ORANGE, style.AQUA, style.VIOLET] * 2


def cards(numbers):
    """(title, example, where it is used) of the eight rule cards."""
    r, cal = numbers["rules"], numbers["calendar"]
    c, age, floor, tie, smoke = r["commission"], r["age"], r["floor"], r["tie"], r["smoker"]
    conversion = dt.date.fromisoformat(numbers["era"]["conversion"])
    new_year = next(d for d, name in cal["holidays"].items() if name == "New Year")
    moved = dt.date.fromisoformat(cal["next_business_day"][new_year])
    born, start = dt.date.fromisoformat(age["birth"]), dt.date.fromisoformat(age["start"])
    factor = float(smoke["factors"][0])
    old = [p for p in numbers["era"]["policies"] if dt.date.fromisoformat(p["signed"]) < conversion]
    old_wrong = sum(not p["java"] for p in old)
    return (
        ("Broker on the day the\nmoney arrived",
         f"{c['policy']}: €{c['premium']} × {float(c['rate']):.0%} = €{c['commission']}", "t0 commission"),
        ("COBOL cuts cents off,\nJava rounds half up",
         f"Switch on {conversion:%-d %b %Y}. Java maths on the old offers: {old_wrong} of {len(old)} wrong",
         "t2, t3, t4"),
        ("COBOL management\nfee: days / 360",
         "Policy started on the 31st, run of 29 Feb: 29 days / 360 (Java: 1/12)", "t3, t4"),
        ("Age = nearest\nbirthday",
         f"Born {born:%-d %b %Y}, start {start:%-d %b %Y}: {age['years']} years {age['months']} months "
         f"→ age {age['age']}", "t2, t3, t4"),
        ("Collect on the next\nTicino business day",
         f"{r['holiday_rules']} holidays (cantonal law), no Good Friday. New Year: "
         f"{dt.date.fromisoformat(new_year):%a %-d %b %Y} → {moved:%a %-d %b}", "t1 due dates"),
        ("Surrender value\nnever below 0",
         f"{floor['policy']} on {dt.date.fromisoformat(floor['date']):%-d %b %Y}: value −€{abs(float(floor['value'])):.2f}"
         f" → surrender €{float(floor['surrender']):.2f}", "t3 surrender value"),
        ("Tie: the cent goes to\nthe pot with a booking",
         f"{tie['policy']}, Dec 2019: two pots at €{float(tie['value']):,.2f} → "
         f"cent to {tie['winner']}", "t3, t4"),
        ("Smoker = “J”\n(German “ja”), not “Y”",
         f"{smoke['codes']['J']:,} people marked J, {smoke['codes']['N']:,} N. Smokers pay "
         f"{factor:g}× the risk charge", "t2, t3, t4"),
    )


def card(fig, x, y, w, h, color, title, example, used):
    """A rule card: coloured edge, title (line breaks given), the real example and the tasks that use it."""
    style.panel(fig, x, y, w, h, fill=style.LIGHT)
    style.panel(fig, x, y, 0.008, h, fill=color, radius=0.004)
    fig.text(x + 0.02, y + h - 0.035, title, fontsize=16, fontweight="bold", va="top", linespacing=1.15)
    below = y + h - 0.035 - 0.042 * (title.count("\n") + 1) - 0.03
    fig.text(x + 0.02, below, textwrap.fill(example, 27), fontsize=13, color=style.INK, va="top", linespacing=1.3)
    fig.text(x + 0.02, y + 0.025, used, fontsize=12, color=color, fontweight="bold", va="bottom")


def draw(numbers):
    fig = style.canvas()
    style.heading(fig, "Eight rules we found in the old system's data",
                  "Each with a real example. The traps: dates, the 2007 system change, rounding, local holidays.",
                  "Examples calculated by our engine from the data (visuals/data/numbers.json); the 29-day example "
                  "is from logs/t3-t4.md.")
    gap = 0.015
    w, h = (0.92 - 3 * gap) / 4, 0.35
    for i, rule in enumerate(cards(numbers)):
        row, col = divmod(i, 4)
        card(fig, 0.04 + col * (w + gap), 0.435 - row * (h + 0.02), w, h, COLORS[i], *rule)
    return style.save_png(fig, "10_rules_found")
