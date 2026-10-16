"""Per-policy features from the legacy tables, joined to the mismatches so that a tree or a plot can explain them.

`policy_features(legacy_dir)` returns one row per policy (index `policy_id`) built once per legacy folder.
`row_dates(task, legacy_dir, frame)` adds the row-level date of keyed tasks (due date, valuation date, year).
`manual_corrections(task, legacy_dir)` lists the policies NREXCP marks as corrected by hand for a task.
"""
import datetime as dt
import functools
import pathlib

import pandas as pd

ERA_SWITCH = dt.date(2007, 8, 11)  # COBOL before, Java from here on (event 800 "system conversion")
MISSING = "?"


def read(legacy_dir, name):
    """A legacy table as trimmed strings."""
    df = pd.read_csv(pathlib.Path(legacy_dir) / f"{name}.csv", sep=";", dtype=str, keep_default_na=False)
    return df.apply(lambda c: c.str.strip())


def day(n):
    """Legacy date CYYMMDD -> date; 0 and 9999999 -> None (invalid days such as 1954-11-31 -> None too)."""
    try:
        n = int(n)
        if n in (0, 9999999):
            return None
        return dt.date(1900 + n // 10000, n // 100 % 100, n % 100)
    except (TypeError, ValueError):
        return None


def raw_ymd(n):
    """CYYMMDD as (year, month, day) without validation."""
    n = int(n)
    return 1900 + n // 10000, n // 100 % 100, n % 100


def era(d):
    if d is None or pd.isna(d):
        return MISSING
    return "cobol" if d < ERA_SWITCH else "java"


def age_years(birth_ymd, at):
    """Completed years between a raw birth (y, m, d) and a date, tolerant of impossible birth days."""
    if at is None or birth_ymd is None:
        return None
    y, m, d = birth_ymd
    return at.year - y - ((at.month, at.day) < (m, d))


def _header(pol):
    """First and current version of every policy header."""
    pol = pol.assign(_v=pol.PH_VRSNR.astype(int)).sort_values(["PH_POLNR", "_v"])
    first = pol.groupby("PH_POLNR").first()
    current = pol.groupby("PH_POLNR").last()
    out = pd.DataFrame(index=first.index)
    out["app_date"] = first.PH_APPDT.map(day)
    out["start_date"] = first.PH_BEGDT.map(day)
    out["end_date"] = first.PH_ENDDT.map(day)
    out["product"] = first.PH_PRDCD
    out["currency"] = first.PH_CCY
    out["frequency"] = first.PH_FREQ
    out["payment_method"] = first.PH_PAYMT
    out["premium"] = first.PH_PREMI.astype(float) / 100
    out["broker"] = first.PH_BRKNR
    out["campaign"] = first.PH_MKTCD.replace("", MISSING)
    out["state"] = current.PH_STATE
    out["n_versions"] = pol.groupby("PH_POLNR").size()
    out["term_years"] = [(e.year - s.year) if s and e else None for s, e in zip(out.start_date, out.end_date)]
    return out


def _tariff(risk, pers):
    """Main risk: tariff key split into its parts, plus the insured person."""
    risk = risk[risk.RK_RSKNR.astype(int) == 1].set_index("RK_POLNR")
    key = risk.RK_TARKEY
    out = pd.DataFrame(index=risk.index)
    out["tariff_key"] = key
    out["tariff_family"] = key.str[:2]
    out["sex_basis"] = key.str[2]
    out["tariff_gen"] = key.str[3:5]
    out["tariff_gen_nr"] = pd.to_numeric(key.str[3:5], errors="coerce")
    out["premium_type"] = key.str[5]
    out["death_option"] = key.str[6]
    out["sum_insured"] = risk.RK_SUMIN.astype(float) / 100
    out["loading"] = risk.RK_LOAD.astype(float) / 10**6
    out["uw_class"] = risk.RK_UWCLS
    ps = pers.set_index("PS_PERNR").reindex(risk.RK_PERNR)
    out["sex"] = ps.PS_SEX.values
    out["smoker"] = ps.PS_SMOKE.values
    out["country"] = ps.PS_CNTRY.values
    out["birth_ymd"] = [raw_ymd(b) if b else None for b in ps.PS_BIRTH.values]
    return out


def _mortality_table(features, chrg):
    """CG_MORTTB of the charge row valid on the application date (fallback: first row of the generation)."""
    chrg = chrg.assign(_fr=chrg.CG_VLDFR.map(day), _to=chrg.CG_VLDTO.map(day).fillna(dt.date.max))
    by_gen = {k: g for k, g in chrg.groupby(["CG_TARFAM", "CG_TARGEN"])}

    def lookup(row):
        g = by_gen.get((row.tariff_family, row.tariff_gen))
        if g is None or row.app_date is None:
            return MISSING
        ok = g[(g._fr <= row.app_date) & (g._to >= row.app_date)]
        return (ok if len(ok) else g).iloc[-1].CG_MORTTB

    return features.apply(lookup, axis=1)


@functools.lru_cache(maxsize=4)
def _features(legacy_dir):
    legacy_dir = pathlib.Path(legacy_dir)
    f = _header(read(legacy_dir, "NRPOLH"))
    f = f.join(_tariff(read(legacy_dir, "NRRISK"), read(legacy_dir, "NRPERS")))
    f = f.join(read(legacy_dir, "NRBROK").set_index("BR_BRKNR").BR_TIER.rename("broker_tier"), on="broker")
    f["mort_table"] = _mortality_table(f, read(legacy_dir, "NRCHRG"))
    excp = read(legacy_dir, "NREXCP")
    f["nrexcp"] = excp.groupby("EX_POLNR").EX_TARGET.agg(lambda s: ",".join(sorted(s))).reindex(f.index)
    f["nrexcp"] = f.nrexcp.fillna("")
    f["age_at_start"] = [age_years(b, s) for b, s in zip(f.birth_ymd, f.start_date)]
    f["era"] = f.app_date.map(era)
    f["app_year"] = [d.year if d else None for d in f.app_date]
    f = f.drop(columns=["birth_ymd"])
    for c in f.columns:  # categorical blanks -> explicit marker, numeric stay NaN
        if f[c].dtype == object and c not in ("app_date", "start_date", "end_date"):
            f[c] = f[c].fillna(MISSING).replace("", MISSING)
    f.index.name = "policy_id"
    return f


def policy_features(legacy_dir) -> pd.DataFrame:
    """One row per policy with the features listed in the module docstring; cached per legacy folder."""
    return _features(str(pathlib.Path(legacy_dir).resolve())).copy()


CATEGORICAL = ["product", "currency", "frequency", "payment_method", "state", "tariff_family", "sex_basis",
               "tariff_gen", "premium_type", "death_option", "uw_class", "sex", "smoker", "country", "broker_tier",
               "mort_table", "era", "row_era"]
NUMERIC = ["premium", "n_versions", "term_years", "sum_insured", "loading", "age_at_start", "tariff_gen_nr",
           "app_year", "row_year"]


def row_dates(task, legacy_dir, frame):
    """Add `row_date` (and `row_era`, `row_year`) to a frame keyed by the task's key columns."""
    if task.startswith("t0"):
        prem = read(legacy_dir, "NRPREM")
        due = {(p, int(n)): day(d) for p, n, d in zip(prem.PR_POLNR, prem.PR_DUENR, prem.PR_DUEDT)}
        rcv = {(p, int(n)): day(d) for p, n, d in zip(prem.PR_POLNR, prem.PR_DUENR, prem.PR_RCVDT)}
        keys = list(zip(frame.policy_id, frame.due_nr))
        frame["row_date"] = [due.get(k) for k in keys]
        frame["received_date"] = [rcv.get(k) for k in keys]
    elif task.startswith("t1"):
        frame["row_date"] = frame["tgt_due_date"]
    elif task.startswith("t3"):
        frame["row_date"] = frame["valuation_date"]
    elif task.startswith("t4"):
        frame["row_date"] = [dt.date(int(y), 12, 31) for y in frame.year]
    else:  # per-policy task: no row-level date
        return frame
    frame["row_era"] = frame.row_date.map(era)
    frame["row_year"] = [d.year if d else None for d in frame.row_date]
    return frame


def manual_corrections(task, legacy_dir):
    """Policies whose NREXCP entry names this task (the official evaluation does not score those rows)."""
    f = policy_features(legacy_dir)
    return set(f.index[f.nrexcp.str.contains(task, regex=False)])
