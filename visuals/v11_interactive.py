"""report/interactive.html: one self-contained companion page with a tab per topic (Plotly from a pinned CDN build).

The page is visuals/interactive_template.html with the theme (theme.css, theme.json) and the numbers
(data/numbers.json, all from our engine and data) written into it.
"""
import json
import re

import style

PAGE = style.HERE.parent / "report/interactive.html"


def change(source):
    """'logs/t0.md [rule] broker as-of the money date (10 wrong)' -> 'broker as-of the money date (10 wrong)'."""
    return re.sub(r"^.*?\] ", "", source).replace("git ", "commit ")


def page_data(numbers):
    """The part of numbers.json the page shows, plus the theme."""
    milestones = [{**m, "change": change(m["source"])} for m in numbers["milestones"]]
    keep = ("examples", "t0", "calendar", "exits", "readiness", "scores")
    return {"theme": style.THEME, "milestones": sorted(milestones, key=lambda m: m["time"]),
            **{k: numbers[k] for k in keep}}


def draw(numbers):
    html = (style.HERE / "interactive_template.html").read_text()
    html = html.replace("/*THEME_CSS*/", (style.HERE / "theme.css").read_text())
    html = html.replace("/*DATA*/", json.dumps(page_data(numbers), separators=(",", ":")))
    PAGE.write_text(html)
    return PAGE
