"""Explain the mismatches of a rule: where are they, what do they have in common, when do they start.

    findings = explain(mm)          # prints the analysis and returns it as a dict for the report

Sections: accuracy, histogram of the diff, groups with a high mismatch rate, a shallow decision tree printed as
rules with support, change points of the mismatch rate over the application date and the row date, worst rows.
"""
import datetime as dt
import math

import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier

from harness import features

DATE_COLS = ["app_date", "start_date", "row_date"]
SHOW_COLS = ["app_date", "tariff_key", "mort_table", "age_at_start", "frequency", "broker_tier", "era", "nrexcp"]


# ---------------------------------------------------------------- histogram
BUCKETS = [("0", lambda d: d == 0), ("+1", lambda d: d == 1), ("-1", lambda d: d == -1),
           ("+2..10", lambda d: (d >= 2) & (d <= 10)), ("-2..-10", lambda d: (d <= -2) & (d >= -10)),
           ("> +10", lambda d: d > 10), ("< -10", lambda d: d < -10)]


def histogram(frame):
    """Counts of the diff per bucket (cents for amounts, days for dates), missing predictions apart."""
    d = frame["diff"]
    present = d.dropna().astype(int)
    out = {name: int(test(present).sum()) for name, test in BUCKETS}
    out["missing"] = int(d.isna().sum())
    return out


# ---------------------------------------------------------------- decision tree
def to_year(d):
    """date -> fractional year, so that a tree threshold reads as a date."""
    if d is None or pd.isna(d):
        return np.nan
    return d.year + (d.timetuple().tm_yday - 1) / 366


def from_year(y):
    year = int(math.floor(y))
    return (dt.date(year, 1, 1) + dt.timedelta(days=round((y - year) * 366))).isoformat()


def design_matrix(frame, max_levels=30, with_dates=False):
    """Numeric matrix for the tree: one-hot categoricals (<= max_levels levels), numerics, optionally dates as years.

    Dates are left out by default so that the tree answers *what* the mismatches have in common (tariff, table,
    age ...) while the change points answer *when* they start; a date split would mask both.
    """
    parts = []
    for col in features.CATEGORICAL:
        if col in frame and frame[col].nunique() <= max_levels and (with_dates or not col.endswith("era")):
            parts.append(pd.get_dummies(frame[col].astype(str), prefix=col, prefix_sep="=", dtype=float))
    for col in features.NUMERIC:
        if col in frame and (with_dates or not col.endswith("_year")):
            parts.append(pd.to_numeric(frame[col], errors="coerce").rename(col).astype(float))
    for col in DATE_COLS:
        if col in frame and with_dates:
            parts.append(frame[col].map(to_year).rename(col + "@year"))
    X = pd.concat(parts, axis=1)
    return X.fillna(X.median(numeric_only=True)).fillna(0.0)


def condition(name, threshold, go_left):
    """A tree split as text: one-hot 'col=val' becomes equality, dates become ISO dates."""
    if "=" in name:
        col, val = name.split("=", 1)
        return f"{col} != {val}" if go_left else f"{col} == {val}"
    if name.endswith("@year"):
        return f"{name[:-5]} {'<=' if go_left else '>'} {from_year(threshold)}"
    return f"{name} {'<=' if go_left else '>'} {threshold:.4g}"


def tree_rules(frame, max_depth=3, min_leaf=3):
    """Fit a shallow tree mismatch-vs-match and return its leaves as rules with raw support counts."""
    y = (~frame.match).astype(int).values
    if y.sum() == 0 or y.sum() == len(y):
        return []
    X = design_matrix(frame)
    clf = DecisionTreeClassifier(max_depth=max_depth, min_samples_leaf=min_leaf, class_weight="balanced",
                                 random_state=0).fit(X.values, y)
    t = clf.tree_
    leaf_of_row = clf.apply(X.values)
    counts = pd.DataFrame({"leaf": leaf_of_row, "bad": y}).groupby("leaf").bad.agg(["size", "sum"])
    rules = []

    def walk(node, path):
        if t.children_left[node] == -1:
            n, bad = counts.loc[node, "size"], counts.loc[node, "sum"]
            rules.append({"rule": " AND ".join(path) or "(all rows)", "support": int(n), "mismatches": int(bad),
                          "rate": bad / n})
            return
        name = X.columns[t.feature[node]]
        thr = t.threshold[node]
        walk(t.children_left[node], path + [condition(name, thr, True)])
        walk(t.children_right[node], path + [condition(name, thr, False)])

    walk(0, [])
    return sorted(rules, key=lambda r: (-r["rate"], -r["mismatches"]))


# ---------------------------------------------------------------- change points
def best_split(signal, min_size):
    """Index, rate before, rate after and z-score of the split with the largest two-proportion z-score."""
    n = len(signal)
    if n < 2 * min_size:
        return None
    cum = np.concatenate([[0], np.cumsum(signal)])
    i = np.arange(min_size, n - min_size + 1)
    p1, p2, p = cum[i] / i, (cum[n] - cum[i]) / (n - i), cum[n] / n
    se = np.sqrt(p * (1 - p) * (1 / i + 1 / (n - i))) + 1e-9
    z = np.abs(p2 - p1) / se
    k = int(z.argmax())
    return int(i[k]), float(p1[k]), float(p2[k]), float(z[k])


def pelt_breakpoints(signal, min_size, max_points=3000):
    """Change points (row indices) of a 0/1 signal: ruptures Pelt solution with l2 cost and a BIC-like penalty.

    Long signals are averaged over equal-count bins first, so that a task with 200k rows stays fast.
    """
    try:
        import ruptures as rpt
    except ImportError:
        return []
    n = len(signal)
    step = max(1, n // max_points)
    binned = signal[: n // step * step].reshape(-1, step).mean(axis=1) if step > 1 else signal
    var = max(binned.var(), 1e-4)
    pen = 3 * var * math.log(len(binned))
    # KernelCPD with a linear kernel is the exact Pelt/l2 solution, implemented in C (Pelt itself is pure Python)
    algo = rpt.KernelCPD(kernel="linear", min_size=max(2, min_size // step), jump=1).fit(binned.reshape(-1, 1))
    return [b * step for b in algo.predict(pen=pen) if b < len(binned)]


def change_points(frame, date_col, min_size=None):
    """Mismatch rate jumps over `date_col`: Pelt segments plus the single most significant split."""
    sub = frame[[date_col, "match"]].dropna(subset=[date_col]).sort_values(date_col)
    n = len(sub)
    if n < 20:
        return {"column": date_col, "n": n, "segments": [], "best": None}
    min_size = min_size or max(10, n // 100)
    signal = (~sub.match).astype(float).values
    dates = sub[date_col].values
    bkps = pelt_breakpoints(signal, min_size)
    edges = [0] + bkps + [n]
    segments = [{"from": dates[a], "to": dates[b - 1], "n": b - a, "rate": float(signal[a:b].mean())}
                for a, b in zip(edges, edges[1:])]
    split = best_split(signal, min_size)
    best = None
    if split:
        i, p1, p2, z = split
        best = {"date": dates[i], "rate_before": p1, "rate_after": p2, "z": z, "significant": z >= 3}
    return {"column": date_col, "n": n, "segments": segments, "best": best}


def era_boundary(frame, date_col, days=90):
    """Mismatch rate of the rows whose date lies within `days` of the COBOL/Java switch, against the overall rate."""
    d = frame[date_col].dropna()
    near = d[(d >= features.ERA_SWITCH - dt.timedelta(days=days)) & (d <= features.ERA_SWITCH + dt.timedelta(days=days))]
    rows = frame.loc[near.index]
    rate = float((~rows.match).mean()) if len(rows) else 0.0
    overall = float((~frame.match).mean())
    return {"column": date_col, "days": days, "rows": len(rows), "mismatches": int((~rows.match).sum()),
            "rate": rate, "overall": overall, "suspicious": len(rows) >= 10 and rate > 2 * overall and rate > 0.02}


# ---------------------------------------------------------------- coverage
def coverage(frame, min_coverage=0.5, stop_at=0.9, max_values=3, top=8):
    """Per categorical feature, the set of most frequent values (<= max_values) that best separates the mismatches.

    Reports coverage of the mismatches against the share of all rows those values hold, best = largest gap between
    the two: a value set holding 25 % of the rows but 100 % of the mismatches is where the missing rule lives.
    """
    bad = frame[~frame.match]
    if bad.empty:
        return []
    out = []
    for col in features.CATEGORICAL + ["tariff_key"]:
        if col not in frame or frame[col].nunique() > 60:
            continue
        ranked = bad[col].value_counts()
        best = None
        for k in range(1, min(max_values, len(ranked)) + 1):  # best prefix of the most frequent values
            values = list(ranked.index[:k])
            covered = int(ranked.iloc[:k].sum())
            rows = int(frame[col].isin(values).sum())
            cov, share = covered / len(bad), rows / len(frame)
            if cov >= min_coverage and cov > share and (best is None or cov - share > best["gap"]):
                best = {"feature": col, "values": [str(v) for v in values], "covered": covered, "coverage": cov,
                        "rows": rows, "share": share, "concentration": cov / share, "gap": cov - share}
            if cov >= stop_at:
                break
        if best:
            out.append(best)
    return sorted(out, key=lambda r: -r["gap"])[:top]


# ---------------------------------------------------------------- group lifts
def group_lifts(frame, min_count=3, min_lift=2.0, top=12):
    """Categorical values whose mismatch rate is at least `min_lift` times the overall rate."""
    overall = (~frame.match).mean()
    out = []
    for col in features.CATEGORICAL + ["app_year", "row_year", "product", "tariff_key"]:
        if col not in frame or frame[col].nunique() > 60:
            continue
        g = frame.groupby(col, dropna=False).match.agg(["size", lambda s: int((~s).sum())])
        g.columns = ["support", "mismatches"]
        g["rate"] = g.mismatches / g.support
        for val, r in g.iterrows():
            if r.support >= min_count and r.mismatches >= 2 and overall and r.rate >= min_lift * overall:
                out.append({"feature": col, "value": val, "support": int(r.support), "mismatches": int(r.mismatches),
                            "rate": r.rate, "lift": r.rate / overall})
    return sorted(out, key=lambda r: -r["lift"])[:top]


# ---------------------------------------------------------------- printing
def fmt_rate(x):
    return f"{100 * x:.1f}%"


def explain(mm, top=10, printer=print):
    """Print the analysis of `mm` (a Mismatches) and return the findings as a dict (used by the report)."""
    f = mm.frame
    lines = []
    say = lines.append
    say(f"{mm.task}: {mm.correct}/{mm.total} exact = {mm.accuracy:.4%}; {mm.total - mm.correct} mismatches, "
        f"{int(f['diff'].isna().sum())} missing predictions, {mm.extra_keys} extra keys; "
        f"{mm.excluded} NREXCP manual corrections not scored")
    unit = "days" if mm.task.startswith("t1") else "cents"
    hist = histogram(f)
    say(f"\n## Diff histogram (predicted - target, {unit})")
    for k, v in hist.items():
        say(f"  {k:>8}: {v:7d}")
    cover = coverage(f)
    say("\n## Where the mismatches concentrate (value sets covering most of them)")
    for r in cover:
        say(f"  {r['feature']} in {{{', '.join(r['values'])}}} covers {r['covered']}/{mm.total - mm.correct} mismatches "
            f"({fmt_rate(r['coverage'])}) within {fmt_rate(r['share'])} of the rows  x{r['concentration']:.1f}")
    if not cover:
        say("  none (no single value covers half of the mismatches)")
    lifts = group_lifts(f)
    say("\n## Groups with a high mismatch rate (lift vs overall)")
    for r in lifts or []:
        say(f"  {r['feature']} = {r['value']!s:8} {r['mismatches']:4d}/{r['support']:<6d} {fmt_rate(r['rate']):>6}"
            f"  lift {r['lift']:.0f}x")
    if not lifts:
        say("  none")
    rules = tree_rules(f)
    say("\n## Decision tree (depth 3) mismatch vs match, leaves as rules")
    for r in rules:
        say(f"  [{r['mismatches']:4d}/{r['support']:<6d} {fmt_rate(r['rate']):>6}] {r['rule']}")
    cps = {}
    for col in ["app_date", "row_date"]:
        if col in f and not (col == "row_date" and f.row_date.equals(f.app_date)):
            cps[col] = change_points(f, col)
    say("\n## Change points of the mismatch rate")
    for col, cp in cps.items():
        say(f"  over {col} ({cp['n']} rows):")
        if len(cp["segments"]) <= 1:
            say("    Pelt: no change point (rate is stable over time)")
        for s in cp["segments"] if len(cp["segments"]) > 1 else []:
            say(f"    Pelt: {s['from']} .. {s['to']}  n={s['n']:<6d} rate {fmt_rate(s['rate'])}")
        b = cp["best"]
        if b:
            verdict = "significant" if b["significant"] else "not significant"
            say(f"    best split at {b['date']}: {fmt_rate(b['rate_before'])} before -> {fmt_rate(b['rate_after'])}"
                f" after (z={b['z']:.1f}, {verdict})")
    boundary = era_boundary(f, "row_date" if "row_date" in f else "app_date")
    say(f"\n## Era boundary check ({boundary['column']} within {boundary['days']} days of {features.ERA_SWITCH})")
    say(f"  window: {boundary['mismatches']}/{boundary['rows']} mismatches = {fmt_rate(boundary['rate'])} vs overall "
        f"{fmt_rate(boundary['overall'])}" + ("  <- the COBOL/Java switch still explains mismatches"
                                             if boundary["suspicious"] else "  (nothing left at the switch)"))
    worst = mm.mismatches.assign(_abs=lambda d: d["diff"].abs()).sort_values("_abs", ascending=False).head(top)
    cols = mm.key_cols + [c for c in worst.columns if c.startswith(("pred_", "tgt_"))] + ["diff"]
    cols += [c for c in SHOW_COLS if c in worst]
    say(f"\n## Top {top} mismatching rows by |diff|")
    say(worst[cols].to_string(index=False) if len(worst) else "  none")
    text = "\n".join(lines)
    if printer:
        printer(text)
    return {"accuracy": mm.accuracy, "correct": mm.correct, "total": mm.total, "histogram": hist, "coverage": cover, "lifts": lifts,
            "rules": rules, "change_points": cps, "era_boundary": boundary, "worst": worst[cols], "text": text}
