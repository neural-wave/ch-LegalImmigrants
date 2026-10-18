"""02_score_climb.gif: accuracy of t0-t4 rising over the build night, with the code readability score beside it.

Milestones come from the team logs and git history (visuals/data/milestones.csv, one source per row). "Estimated"
means the rows our outlier finder (t5) marks as hand edits are left out, as the official scoring leaves out manual
corrections; the measured train score counts them as wrong.
"""
import datetime as dt

import matplotlib.dates as mdates

import style
from style import plt

TASKS = {"t0": "t0\nCommission", "t1": "t1\nNext due\ndates", "t2": "t2\nMaturity\nvalue",
         "t3": "t3\nSurrender\nvalue", "t4": "t4\nAnnual\nstatement"}
FLOOR = 90.0  # the accuracy axis starts here: below it every bar looks the same
CHAPTERS = (  # (end of the chapter, what changed): the GIF holds on the state after each one
    ("2026-10-16 20:35", "t0: the broker must be taken on the day the money arrived"),
    ("2026-10-16 22:34", "t1 and t2: due dates on Ticino business days, offers in COBOL or Java maths"),
    ("2026-10-16 23:29", "t3 and t4: every booking of every policy replayed, charges calculated"),
    ("2026-10-17 03:33", "Last gaps closed: every row still wrong is a hand edit"),
    ("2026-10-17 07:16", "One small rule per file: readability 100, answers unchanged"),
)


def steps(milestones):
    """[(time, {series: (measured, estimated)})] after each distinct milestone time."""
    state, out = {}, []
    times = sorted({m["time"] for m in milestones})
    for t in times:
        for m in (m for m in milestones if m["time"] == t):
            measured, estimated = state.get(m["series"], (None, None))
            if m["kind"] == "estimated":
                estimated = float(m["value"])
            else:
                measured = float(m["value"])
            state[m["series"]] = (measured, estimated)
        out.append((dt.datetime.fromisoformat(t), dict(state)))
    return out


def label(v):
    """99.9956 -> '99.996%', 91.18 -> '91.18%', 100 -> '100%'."""
    return "100%" if v >= 100 else f"{v:.3f}%" if v >= 99.9 else f"{v:.2f}%" if v >= 99 else f"{v:.1f}%"


def draw(numbers):
    history = steps(numbers["milestones"])
    check_final(history[-1][1], numbers["scores"])
    fig = style.canvas()
    style.heading(fig, "From first try to every rule found, in one night",
                  "Share of training rows we get exactly right (to the cent, to the day), task by task.",
                  "Sources: team logs (logs/*.md) and git history, see visuals/data/milestones.csv. "
                  "* estimated: rows our outlier finder marks as hand edits are left out, like the official scoring.")
    bars = fig.add_axes([0.085, 0.22, 0.54, 0.54])
    mi = fig.add_axes([0.71, 0.22, 0.26, 0.5])
    legend = [plt.Rectangle((0, 0), 1, 1, color=style.BLUE),
              plt.Rectangle((0, 0), 1, 1, facecolor=style.BLUE_LIGHT, hatch="//", edgecolor=style.SURFACE)]
    fig.legend(legend, ["measured on the training data", "estimated*: hand edits left out"], loc="lower left",
               bbox_to_anchor=(0.06, 0.045), ncol=2, fontsize=14)
    clock = fig.text(0.97, 0.925, "", fontsize=24, ha="right", fontweight="bold", color=style.INK_2)

    caption = fig.text(style.LAYOUT["margin_x"], 0.815, "", fontsize=style.SIZE["step"], color=style.INK,
                       fontweight="bold")
    states = [chapter_state(history, end) for end, _ in CHAPTERS]

    def update(step, progress):
        """Bars move into the chapter's state; clock, caption and numbers appear once it is settled."""
        when, now = states[step]
        settled = progress is None
        shown_when = when if settled else states[step - 1][0]
        clock.set_text(shown_when.strftime("%a %H:%M"))
        caption.set_text(CHAPTERS[step if settled else step - 1][1])
        before = states[step - 1][1] if step else {}
        draw_bars(bars, before, now, 1.0 if settled else style.ease(progress), settled)
        draw_mi(mi, [(t, s["MI"][0]) for t, s in history if "MI" in s and t <= shown_when], history)

    still = (len(CHAPTERS) - 1, None)
    return style.save_gif(fig, "02_score_climb", update, style.steps(len(CHAPTERS), hold=22), still=still)


def chapter_state(history, end):
    """(time, state) of the last milestone at or before the chapter's end."""
    end = dt.datetime.fromisoformat(end)
    return [(t, s) for t, s in history if t <= end][-1]


def check_final(final, scores):
    """Warn if the last logged score differs from what the code scores now."""
    for task, score in scores.items():
        series, now = task[:2], 100 * score["all"]["correct"] / score["all"]["rows"]
        measured = final[series][0]
        if abs(now - measured) > 0.006:
            print(f"warning: {series} logged {measured} but scores {now:.4f} now")


def draw_bars(ax, before, now, t, settled):
    """Five bars, each between its previous and new value (t from 0 to 1); value labels only when settled."""
    ax.clear()
    ax.set_ylim(FLOOR, 100.6)
    ax.set_xlim(-0.6, 4.6)
    ax.set_yticks([90, 92, 94, 96, 98, 100])
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    ax.set_xticks(range(5), TASKS.values(), fontsize=14)
    ax.tick_params(axis="x", length=0)
    ax.grid(axis="x", visible=False)
    ax.set_ylabel("Rows exactly right (axis starts at 90%)")
    for x, series in enumerate(TASKS):
        old = shown_value(before.get(series))
        measured, estimated = now.get(series, (None, None))
        new = shown_value((measured, estimated))
        if new is None:
            if settled:
                ax.text(x, FLOOR + 0.3, "not\nstarted", ha="center", fontsize=13, color=style.MUTED)
            continue
        v = new if old is None else old + (new - old) * t
        color = style.BLUE_LIGHT if estimated else style.BLUE
        ax.bar(x, max(v, FLOOR) - FLOOR, bottom=FLOOR, width=0.62, color=color,
               hatch="//" if estimated else None, edgecolor=style.SURFACE, linewidth=0)
        if estimated and measured is not None:
            ax.bar(x, max(measured, FLOOR) - FLOOR, bottom=FLOOR, width=0.62, color=style.BLUE)
        if not settled:
            continue
        top = max(v, FLOOR)
        text = label(new) + ("*" if estimated else "")  # the logged value, never an in-between one
        ax.text(x, top + (0.9 if new < FLOOR else 0.12), text, ha="center", va="bottom", fontsize=17,
                fontweight="bold")
        if new < FLOOR:
            ax.text(x, FLOOR + 0.25, "(below the axis)", ha="center", fontsize=12, color=style.INK_2)
        elif estimated and measured is not None and measured < 100:
            ax.text(x, FLOOR + 0.35, f"measured\n{label(measured)}", ha="center", fontsize=12, color=style.SURFACE)


def shown_value(pair):
    """The bar height: the estimated score when known, else the measured one."""
    if not pair:
        return None
    measured, estimated = pair
    return estimated if estimated is not None else measured


def draw_mi(ax, points, history):
    """Code readability (maintainability index, 0-100) over the night, drawn up to now."""
    ax.clear()
    ax.set_ylim(70, 102)
    ax.set_xlim(history[0][0].replace(hour=23, minute=59), history[-1][0] + dt.timedelta(minutes=30))
    ax.xaxis.set_major_locator(mdates.HourLocator(byhour=[0, 2, 4, 6, 8]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.set_title("Code readability score\n(maintainability index, 0–100)", fontsize=15, loc="left",
                 color=style.INK, pad=10)
    if not points:
        ax.text(0.5, 0.5, "cleanup starts\nafter the rules work", transform=ax.transAxes, ha="center",
                fontsize=14, color=style.MUTED)
        return
    times, values = zip(*points)
    ax.plot(times, values, color=style.ORANGE, drawstyle="steps-post")
    ax.plot(times[-1], values[-1], "o", color=style.ORANGE, markersize=9)
    ax.annotate(f"{values[-1]:.1f}", (times[-1], values[-1]), xytext=(-8, 10), textcoords="offset points",
                ha="right", fontsize=17, fontweight="bold")
    if len(points) > 1:
        ax.annotate(f"{values[0]:.1f}", (times[0], values[0]), xytext=(4, -22), textcoords="offset points",
                    fontsize=14, color=style.INK_2)
