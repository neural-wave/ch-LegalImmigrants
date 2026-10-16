"""Save an explain run as markdown plus PNGs in harness/reports/<task>/."""
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from harness import paths  # noqa: E402


def rate_by_period(frame, date_col, freq="QS"):
    """Mismatch rate and row count per period of `date_col`."""
    sub = frame[[date_col, "match"]].dropna(subset=[date_col])
    sub = sub.assign(period=pd.to_datetime(sub[date_col]).dt.to_period("Q" if freq == "QS" else "M"))
    g = sub.groupby("period").match.agg(["size", lambda s: float((~s).mean())])
    g.columns = ["rows", "rate"]
    return g


def plot_rate(frame, date_col, path, title):
    g = rate_by_period(frame, date_col)
    fig, ax = plt.subplots(figsize=(10, 3.6))
    ax.bar(g.index.to_timestamp(), 100 * g.rate, width=80, color="#4C72B0")
    ax.set_ylabel("mismatch rate (%)")
    ax.set_title(title)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def plot_histogram(hist, path, unit):
    fig, ax = plt.subplots(figsize=(7, 3.4))
    keys = [k for k in hist if k != "0"]
    ax.bar(keys, [hist[k] for k in keys], color="#DD8452")
    ax.set_ylabel("rows")
    ax.set_title(f"Mismatches by diff ({unit}); exact rows not shown: {hist['0']}")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def write_report(mm, findings, out_dir=None, label=""):
    """Write report.md, mismatches.csv and the PNGs; returns the folder."""
    out = pathlib.Path(out_dir or paths.REPORTS / mm.task[:2])
    out.mkdir(parents=True, exist_ok=True)
    unit = "days" if mm.task.startswith("t1") else "cents"
    plot_rate(mm.frame, "app_date", out / "mismatch_rate_by_app_date.png", f"{mm.task}: mismatch rate by application date")
    images = ["mismatch_rate_by_app_date.png"]
    if "row_date" in mm.frame and not mm.frame.row_date.equals(mm.frame.app_date):
        plot_rate(mm.frame, "row_date", out / "mismatch_rate_by_row_date.png", f"{mm.task}: mismatch rate by row date")
        images.append("mismatch_rate_by_row_date.png")
    plot_histogram(findings["histogram"], out / "diff_histogram.png", unit)
    images.append("diff_histogram.png")
    mm.mismatches.to_csv(out / "mismatches.csv", index=False)
    md = [f"# Harness report: {mm.task}" + (f" ({label})" if label else ""), "",
          f"Accuracy **{mm.correct}/{mm.total} = {mm.accuracy:.4%}** (exact rows, scoring.py semantics)", "",
          "```", findings["text"], "```", ""]
    md += [f"![{img}]({img})\n" for img in images]
    md.append("Full list of mismatching rows with features: `mismatches.csv`.")
    (out / "report.md").write_text("\n".join(md), encoding="utf-8")
    return out
