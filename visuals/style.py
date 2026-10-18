"""One look for every visual, read from theme.json (shared with theme.css, the report and the video).

Palette (validated for colour-blind readers): blue, orange, aqua, violet in that fixed order, red for wrong rows,
grey for context. Every series also gets a direct text label.

Animations are built from steps: each step moves for at most `move_s` and then holds, fully settled, for `hold_s`
(theme.json "motion"). Headings and numbers that describe a step are only drawn once the step is settled.
"""
import json
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.animation import PillowWriter  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "out"
THEME = json.loads((HERE / "theme.json").read_text())

C, SIZE, LAYOUT, MOTION = THEME["color"], THEME["size_pt"], THEME["layout"], THEME["motion"]
SURFACE, INK, INK_2, MUTED, GRID, AXIS = C["surface"], C["ink"], C["ink_2"], C["muted"], C["grid"], C["axis"]
BLUE, ORANGE, AQUA, VIOLET = C["blue"], C["orange"], C["aqua"], C["violet"]
RED, GREY, LIGHT, BLUE_LIGHT = C["wrong"], C["grey"], C["panel"], C["blue_light"]

WIDTH, HEIGHT = THEME["canvas"]["width_in"], THEME["canvas"]["height_in"]
FPS = THEME["canvas"]["fps"]
HOLD, MOVE, LAST = (round(MOTION[k] * FPS) for k in ("hold_s", "move_s", "last_hold_s"))

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "font.family": THEME["font"]["family"], "font.size": SIZE["body"],
    "text.color": INK, "axes.labelcolor": INK_2, "xtick.color": INK_2, "ytick.color": INK_2,
    "xtick.labelsize": SIZE["tick"], "ytick.labelsize": SIZE["tick"], "axes.labelsize": SIZE["label"],
    "axes.edgecolor": AXIS, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
    "legend.frameon": False, "lines.linewidth": 2.5,
})


def canvas():
    """A blank 16:9 figure."""
    return plt.figure(figsize=(WIDTH, HEIGHT))


def heading(fig, title, subtitle=None, source=None):
    """Title (one clear message), a plain subtitle and a small source line at the bottom."""
    x = LAYOUT["margin_x"]
    fig.text(x, LAYOUT["title_y"], title, fontsize=SIZE["title"], fontweight="bold", color=INK, va="baseline")
    if subtitle:
        fig.text(x, LAYOUT["subtitle_y"], subtitle, fontsize=SIZE["subtitle"], color=INK_2, va="baseline")
    if source:
        fig.text(x, LAYOUT["source_y"], source, fontsize=SIZE["source"], color=MUTED, va="baseline")


def save_png(fig, name, close=True):
    """visuals/out/<name>.png at 1920 x 1080."""
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{name}.png"
    fig.savefig(path, dpi=THEME["canvas"]["png_dpi"])
    if close:
        plt.close(fig)
    return path


def steps(count, hold=HOLD, move=MOVE, last=LAST, first_move=False):
    """Frames of a step animation: [(step, progress)], progress in (0, 1) while moving, None once settled.

    Step 0 starts settled unless `first_move`; every step holds `hold` frames, the last one `last` frames.
    """
    frames = []
    for s in range(count):
        if s or first_move:
            frames += [(s, (i + 1) / (move + 1)) for i in range(move)]
        frames += [(s, None)] * (last if s == count - 1 else hold)
    return frames


def save_gif(fig, name, update, frames, still=None):
    """visuals/out/<name>.gif from update(*frame) for every frame (loops; the last frame is the held end state).

    `still` is the frame to also save as visuals/out/<name>.png for the report (a settled one).
    """
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{name}.gif"
    writer = PillowWriter(fps=FPS)
    with writer.saving(fig, str(path), dpi=THEME["canvas"]["gif_dpi"]):
        for frame in frames:
            update(*frame)
            writer.grab_frame()
    if still is not None:
        update(*still)
        save_png(fig, name, close=False)
    plt.close(fig)
    return path


def ease(t):
    """Smooth 0 -> 1 (slow start and end) for t in [0, 1]."""
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def euros(x, decimals=0):
    """12345.6 -> '€12,346' (decimals=0) or '€12,345.60'."""
    return f"€{x:,.{decimals}f}"


def panel(fig, x, y, w, h, fill=None, edge=None, radius=0.018, width=2.5):
    """A rounded card in figure fractions (bottom-left corner x, y)."""
    from matplotlib.patches import FancyBboxPatch
    fig.patches.append(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={radius}",
                                      transform=fig.transFigure, facecolor=fill or SURFACE,
                                      edgecolor=edge or "none", linewidth=width if edge else 0, zorder=0))


def arrow(fig, start, end, color=None, rad=0.0, lw=3):
    """An arrow between two points in figure fractions."""
    from matplotlib.patches import FancyArrowPatch
    fig.patches.append(FancyArrowPatch(start, end, transform=fig.transFigure, arrowstyle="-|>", mutation_scale=26,
                                       color=color or INK_2, linewidth=lw, connectionstyle=f"arc3,rad={rad}"))
