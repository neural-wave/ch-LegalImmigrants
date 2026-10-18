"""07_architecture.png: our approach as a loop, with the real numbers of the t0 commission rule.

Lab (offline, agentic AI and machine learning help): 1 compare with Neuron's answers (lab/diff.py), 2 find the pattern
(decision tree, lab/miner.py), 3 test the options (lab/search.py with a held-back 20%), 4 keep the plain rule.
Factory (what we hand in, my_solution/): plain Python, no AI, no target files. Its answers go back into step 1.
"""
import style

ORANGE_ZONE, BLUE_ZONE = "#fdeee7", "#eaf2fc"
CARD_W, CARD_H, CARD_Y, GAP, X0 = 0.155, 0.43, 0.29, 0.018, 0.05


def steps(numbers):
    """(title, big number, colour, caption) of the four loop steps, from our numbers."""
    t0, search = numbers["t0"], numbers["search"]
    share = t0["paid_before_broker_change"] / t0["naive_wrong"]
    return (("Compare\nwith Neuron", f"{t0['naive_wrong']:,}", style.RED,
             f"rows wrong of {t0['rows']:,}\nfirst guess: the broker\nthe policy has today"),
            ("Find the\npattern", f"{share:.1%}", style.ORANGE,
             "of the wrong rows were\npaid before the broker\nchanged (decision tree)"),
            ("Test the\noptions", f"{search['candidates']}", style.BLUE,
             f"candidate rules in {search['seconds']:.0f} s,\nchecked on a held-back\n20% of policies"),
            ("Keep the\nplain rule", f"{t0['shipped_wrong']}", style.VIOLET,
             "rows left: hand edits.\nRule: the broker on the\nday the money arrived"))


def card(fig, x, n, title, big, color, caption):
    """One numbered loop step."""
    style.panel(fig, x, CARD_Y, CARD_W, CARD_H, fill=style.SURFACE, edge=style.ORANGE)
    top = CARD_Y + CARD_H
    fig.text(x + 0.027, top - 0.055, str(n), fontsize=20, fontweight="bold", color=style.SURFACE, ha="center",
             va="center", bbox={"boxstyle": "circle,pad=0.3", "facecolor": style.ORANGE, "edgecolor": "none"})
    fig.text(x + 0.055, top - 0.055, title, fontsize=15, fontweight="bold", va="center", linespacing=1.1)
    fig.text(x + CARD_W / 2, CARD_Y + 0.2, big, fontsize=40, fontweight="bold", color=color, ha="center",
             va="center")
    fig.text(x + CARD_W / 2, CARD_Y + 0.085, caption, fontsize=12, color=style.INK_2, ha="center", va="center",
             linespacing=1.3)


def draw(numbers):
    fig = style.canvas()
    style.heading(fig, "Our approach: a loop, shown on a real example",
                  "Finding the commission rule (t0). AI and machine learning help in the lab; "
                  "what we hand in is plain Python.",
                  "Lab: lab/diff.py, lab/miner.py, lab/search.py. Factory: my_solution/ (standard library only). "
                  "Numbers from visuals/data/numbers.json.")
    style.panel(fig, 0.03, 0.09, 0.71, 0.715, fill=ORANGE_ZONE)
    style.panel(fig, 0.76, 0.09, 0.21, 0.715, fill=BLUE_ZONE)
    fig.text(0.05, 0.765, "LAB", fontsize=18, fontweight="bold", color=style.ORANGE, va="center")
    fig.text(0.095, 0.765, "offline · agentic AI and machine learning help here", fontsize=14, color=style.INK_2,
             va="center")
    fig.text(0.775, 0.765, "FACTORY", fontsize=18, fontweight="bold", color=style.BLUE, va="center")
    fig.text(0.775, 0.73, "what we hand in", fontsize=14, color=style.INK_2, va="center")
    for n, step in enumerate(steps(numbers), 1):
        x = X0 + (n - 1) * (CARD_W + GAP)
        card(fig, x, n, *step)
        if n > 1:
            style.arrow(fig, (x - GAP + 0.002, CARD_Y + CARD_H / 2), (x - 0.002, CARD_Y + CARD_H / 2), style.ORANGE)
    factory(fig)
    last = X0 + 3 * (CARD_W + GAP) + CARD_W
    style.arrow(fig, (last + 0.003, CARD_Y + CARD_H / 2), (0.773, CARD_Y + CARD_H / 2), style.INK, lw=4)
    style.arrow(fig, (0.865, 0.255), (X0 + CARD_W / 2, CARD_Y - 0.008), style.BLUE, rad=-0.12, lw=3)
    fig.text(0.42, 0.13, "the factory's answers go back into step 1, for the next rule", fontsize=14,
             color=style.BLUE, ha="center", fontweight="bold")
    return style.save_png(fig, "07_architecture")


def factory(fig):
    """The factory zone: the plain rules and their answers."""
    style.panel(fig, 0.775, 0.4, 0.182, 0.29, fill=style.SURFACE, edge=style.BLUE)
    fig.text(0.866, 0.645, "Plain Python rules", fontsize=15, fontweight="bold", ha="center", va="center")
    for i, line in enumerate(("one small rule\n   per file", "no AI inside", "never reads\n   the answers")):
        fig.text(0.787, (0.585, 0.522, 0.465)[i], "✓ " + line, fontsize=13, color=style.INK, va="center")
    style.arrow(fig, (0.866, 0.398), (0.866, 0.345), style.BLUE)
    style.panel(fig, 0.775, 0.26, 0.182, 0.08, fill=style.BLUE)
    fig.text(0.866, 0.3, "Answers t0–t5", fontsize=15, fontweight="bold", color=style.SURFACE, ha="center",
             va="center")
