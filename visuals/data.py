"""Every number the visuals show, calculated from our engine (neuron/, tasks/) and the challenge data.

Run through make_all.py. The result is written to visuals/data/numbers.json, so the report can quote the exact values
and the charts can be redrawn without a new run (`make_all.py --reuse`). Score milestones over the build come from
the team logs and git history: they are transcribed with their source in visuals/data/milestones.csv.

Policy BL10000013 (01, 05) is replayed on its own from NRBOOK with the same functions t3 and t4 use; the amounts of
its premiums and charges are calculated by the engine (NRBOOK leaves them blank).
"""
import collections
import csv
import datetime as dt
import json
import pathlib
import sys
from decimal import Decimal

ROOT = pathlib.Path(__file__).resolve().parents[1]
KIT = ROOT / "LifewareChallenge/participants/starter_kit"
LEGACY, TARGETS = KIT.parent / "legacy", KIT.parent / "targets"
DATA = ROOT / "visuals/data"
sys.path[:0] = [str(KIT), str(KIT / "my_solution"), str(ROOT / "lab")]

import core  # noqa: E402  (lab: diff frames and context features)
import scoring  # noqa: E402
import submission  # noqa: E402
from neuron.contract import contract  # noqa: E402
from neuron.data import grouped  # noqa: E402
from neuron.funds.bookings import read_bookings  # noqa: E402
from neuron.funds.account import Account  # noqa: E402
from neuron.funds.replay import accounts, replay  # noqa: E402
from neuron.legacy import legacy  # noqa: E402
from neuron.statement_years import statement_years  # noqa: E402
from neuron.calendar.business_days import next_business_day  # noqa: E402
from neuron.calendar.holidays import holidays  # noqa: E402
from neuron.valuation import pot_value  # noqa: E402
from tasks.t3_surrender_value import policy_value, surrender_values  # noqa: E402
from tasks.t4_annual_statement import statement  # noqa: E402

L = str(LEGACY)
POLICY = "BL10000013"
SURRENDER_DATES = (dt.date(2020, 4, 30), dt.date(2025, 12, 31))
STATEMENT_YEAR = 2021
STATEMENT_COLUMNS = ("premiums", "entry", "admin", "management", "risk", "total")
EXIT_KINDS = ("SUR", "DTH")  # NRBOOK customer orders that end a policy: surrender, death


def iso(legacy_date):
    """Legacy CYYMMDD int -> ISO date text."""
    n = int(legacy_date)
    return dt.date(1900 + n // 10000, n // 100 % 100, n % 100).isoformat()


def month_ends(start, end):
    """Last day of every month from start's month to end's month."""
    d = dt.date(start.year, start.month, 1)
    while d <= end:
        nxt = dt.date(d.year + d.month // 12, d.month % 12 + 1, 1)
        yield nxt - dt.timedelta(days=1)
        d = nxt


# ---------------------------------------------------------------- 01 and 05: one policy's life

def one_policy(policy_id):
    """(Contract, replayed booking rows, Account) of one policy, replayed alone."""
    bookings = next(b for pid, b in read_bookings(L) if pid == policy_id)
    policy = contract(L, policy_id)
    rows = replay(policy, bookings)  # same steps as neuron/funds/replay.py account()
    return policy, rows, Account(policy, rows)


def policy_life(policy_id=POLICY):
    """The life of the showcase policy (01, 05)."""
    return policy_story(policy_id, *one_policy(policy_id), SURRENDER_DATES)


def policy_story(policy_id, policy, rows, acc, valuation_dates):
    """Month by month: value per fund, premiums paid so far, units bought and charges taken; switches, holidays,
    surrender values on the valuation dates the policy has, and every annual statement."""
    months = collections.defaultdict(lambda: collections.defaultdict(Decimal))
    premium_events = set()
    for r in rows:
        month = iso(r.trade_date)[:7]
        if r.kind == "PRM":
            months[month]["units_bought"] += r.units
            if r.event not in premium_events:
                premium_events.add(r.event)
                months[iso(r.money_date)[:7]]["premium"] += policy.premiums[r.event]
        elif r.kind in ("ADM", "AMC", "RSK"):
            months[month][r.kind] += r.amount
            months[month]["units_cancelled"] -= r.units
    funds = sorted({r.fund for r in rows})
    series, paid = [], Decimal(0)
    last = min(dt.date(2025, 12, 31), dt.date.fromisoformat(iso(max(r.trade_date for r in rows))))
    for end in month_ends(policy.start, last):
        m, d = months[end.isoformat()[:7]], legacy(end)
        paid += m["premium"]
        per_fund = collections.defaultdict(Decimal)
        for (fund, _), units in acc.holdings(d).items():
            per_fund[fund] += pot_value(policy, fund, units, d, d)
        series.append({"month": end.isoformat()[:7], "paid": str(paid), "premium": str(m["premium"]),
                       "value": str(policy_value(acc, d)), **{f: str(per_fund[f]) for f in funds},
                       "units_bought": str(m["units_bought"]), "units_cancelled": str(m["units_cancelled"]),
                       **{k: str(m[k]) for k in ("ADM", "AMC", "RSK")}})
    switches = collections.defaultdict(dict)
    for r in rows:
        if r.kind in ("SWO", "SWI"):
            switches[r.event]["date"] = iso(r.trade_date)
            switches[r.event]["from" if r.kind == "SWO" else "to"] = r.fund
    holiday = [v for v in policy.versions if v["PH_STATE"].strip() == "30"]
    surrender = dict(surrender_values(policy_id, acc, list(valuation_dates)))
    asset = {r["FD_FNDID"].strip(): r["FD_ASSCL"].strip() for r in core.table(L, "NRFUND")}
    return {
        "policy": policy_id, "currency": policy.currency.strip(), "start": policy.start.isoformat(),
        "monthly_premium": str(next(iter(policy.premiums.values()))),
        "funds": {f: asset[f] for f in funds}, "months": series,
        "switches": sorted(switches.values(), key=lambda s: s["date"]),
        "holiday": [iso(holiday[0]["PH_VLDFR"]), iso(holiday[-1]["PH_VLDTO"])] if holiday else None,
        "holidays": [[iso(v["PH_VLDFR"]), iso(v["PH_VLDTO"])] for v in holiday],
        "surrender": [{"date": d.isoformat(), "value": str(policy_value(acc, legacy(d))),
                       "surrender": str(surrender[policy_id, d])} for d in valuation_dates
                      if (policy_id, d) in surrender],
        "statements": {y: dict(zip(STATEMENT_COLUMNS, map(str, statement(acc.totals, y))))
                       for y in statement_years(policy)},
        "statement": dict(zip(STATEMENT_COLUMNS,
                              map(str, statement(acc.totals, STATEMENT_YEAR)))) | {"year": STATEMENT_YEAR},
    }


# ---------------------------------------------------------------- 03: how the t0 rule was found

def t0_discovery():
    """Naive t0 (broker of today's policy version) vs the shipped rule, and the decision tree's first split."""
    from sklearn.tree import DecisionTreeClassifier
    import miner
    from diff import feature_columns
    naive = core.diff_frame("t0_commission", "variants.t0_commission:t0_commission", {"broker_date": "current"})
    shipped = core.diff_frame("t0_commission", None, {})
    features = [f for f in feature_columns(naive) if f != "exception_listed"]
    x, info = miner.encode(naive, features)
    fit = ~naive["holdout"]  # like lab/miner.py: the tree learns on the 80% search policies only
    tree = DecisionTreeClassifier(max_depth=1, random_state=0).fit(x[fit], ~naive["ok"][fit])
    split = info[tree.tree_.feature[0]][0]
    wrong = naive[~naive["ok"]]
    leaf = naive[split].fillna(False).astype(bool)
    left = shipped[~shipped["ok"]]
    before_change = wrong["broker_changed"].fillna(False).astype(bool) & wrong["before_current_version"].astype(bool)
    return {
        "rows": len(naive), "naive_wrong": len(wrong), "shipped_wrong": len(left),
        "paid_before_broker_change": int(before_change.sum()),
        "split_feature": split,
        "split_yes_rows": int(leaf.sum()), "split_yes_wrong": int((leaf & ~naive["ok"]).sum()),
        "split_no_rows": int((~leaf).sum()), "split_no_wrong": int((~leaf & ~naive["ok"]).sum()),
        "points": [{"date": str(r.rcv_date), "delta": float(r.delta), "split": bool(leaf[i]),
                    "fixed": bool(shipped.loc[i, "ok"])} for i, r in wrong.iterrows()],
        "left": [{"key": f"{r.policy_id} #{r.key_due_nr}", "date": str(r.rcv_date), "delta": float(r.delta),
                  "listed": bool(r.exception_listed)} for _, r in left.iterrows()],
    }


# ---------------------------------------------------------------- 04: the COBOL -> Java change

def t2_with_conversion(conversion):
    """t2 outputs with the COBOL -> Java switch moved to `conversion` (0: Java for all, 9999999: COBOL for all)."""
    import neuron.contract
    real = neuron.contract.conversion_date
    neuron.contract.conversion_date = (lambda _: conversion) if conversion is not None else real
    neuron.contract.contract.cache_clear()
    try:
        return submission.t2_projected_maturity_value(L)
    finally:
        neuron.contract.conversion_date = real
        neuron.contract.contract.cache_clear()


def system_change():
    """Per policy of the t2 targets: offer signing date and whether each era variant gets its value right."""
    target = scoring.read_targets(str(TARGETS), "t2_projected_maturity_value")
    signed = {pid: iso(min(v, key=lambda r: int(r["PH_VRSNR"]))["PH_APPDT"])
              for pid, v in grouped(L, "NRPOLH", "PH_POLNR").items() if pid in target}
    runs = {"ours": None, "java": 0, "cobol": 9999999}
    outputs = {name: t2_with_conversion(c) for name, c in runs.items()}
    return {"conversion": "2007-08-11",
            "policies": [{"signed": signed[pid], **{n: outputs[n].get(pid) == target[pid] for n in runs}}
                         for pid in sorted(target)]}


# ---------------------------------------------------------------- 06: t1 calendar

HOLIDAY_NAMES = {(1, 1): "New Year", (1, 6): "Epiphany", (3, 19): "St Joseph", (5, 1): "Labour Day",
                 (6, 29): "Sts Peter and Paul", (8, 1): "National Day", (8, 15): "Assumption",
                 (11, 1): "All Saints", (12, 8): "Immaculate Conception", (12, 25): "Christmas",
                 (12, 26): "St Stephen"}
EASTER_NAMES = ("Easter Monday", "Ascension", "Whit Monday", "Corpus Christi")  # holidays.EASTER_HOLIDAYS order


def holiday_name(d):
    """Name of a Ticino holiday from neuron/calendar/holidays.py (fixed date or days after Easter)."""
    from neuron.calendar.easter import easter
    from neuron.calendar.holidays import EASTER_HOLIDAYS
    moving = {easter(d.year) + dt.timedelta(days=n): name for n, name in zip(EASTER_HOLIDAYS, EASTER_NAMES)}
    return HOLIDAY_NAMES.get((d.month, d.day)) or moving[d]


def calendar():
    """t1 due and collection dates per day for the year after the extract date, with Ticino holidays."""
    extract = scoring.EXTRACT_DATE
    result = submission.t1_next_due_dates(L, extract)
    due, collected, moved = collections.Counter(), collections.Counter(), 0
    for due_date, collection in result.values():
        due[due_date.isoformat()] += 1
        collected[collection.isoformat()] += 1
        moved += collection != due_date
    end = dt.date(extract.year + 1, extract.month, extract.day)
    days = [extract + dt.timedelta(days=i) for i in range(1, (end - extract).days + 1)]
    hol = sorted(h for y in {d.year for d in days} for h in holidays(y) if extract < h <= end)
    return {"extract": extract.isoformat(), "rows": len(result), "moved": moved, "due": dict(due),
            "collected": dict(collected), "holidays": {h.isoformat(): holiday_name(h) for h in hol},
            "next_business_day": {h.isoformat(): next_business_day(h).isoformat() for h in hol}}


# ---------------------------------------------------------------- 02 and 08: scores and the unseen-policy proof

def scores():
    """Per task: train accuracy with and without the rows t5 flags as hand edits, also split 80 / 20 by core.holdout."""
    flagged = scoring.normalize_outliers(submission.t5_outlier_detection(L, str(TARGETS)))
    out = {}
    for task in list(scoring.TASKS)[:5]:
        target = scoring.read_targets(str(TARGETS), task)
        mine = scoring.normalize(task, getattr(submission, task)(L, *scoring.arguments(task, target)))
        excluded = {key for t, key in flagged if t == task}
        groups = {"all": target, "check": {}, "rest": {}}
        for key, value in target.items():
            groups["check" if core.holdout(core.policy_of(key)) else "rest"][key] = value
        out[task] = {g: {"rows": len(t), "correct": scoring.accuracy(task, mine, t)[0],
                         "correct_est": scoring.accuracy(task, mine, t, excluded)[0],
                         "rows_est": scoring.accuracy(task, mine, t, excluded)[1]} for g, t in groups.items()}
        out[task]["hand_edits"] = len(excluded)
    return out


def exits():
    """Policies that left by surrender or death (SUR / DTH in NRBOOK): how many hold exactly 0 units after it."""
    train = set(scoring.read_targets(str(TARGETS), "t2_projected_maturity_value"))
    count = collections.Counter()
    exit_events = exit_bookings()
    for pid, acc in accounts(L).items():
        if not exit_events.get(pid, set()) - acc.policy.skipped:  # no counted (non-reversed) exit booking
            continue
        group = "train" if pid in train else "unseen"
        count[group, "exited"] += 1
        count[group, "zero"] += all(u == 0 for u in acc.holdings(9999999).values())
    return {g: {"exited": count[g, "exited"], "zero": count[g, "zero"]} for g in ("train", "unseen")}


def exit_bookings():
    """{policy: {event}} of the surrender and death bookings in NRBOOK (their units come from the export)."""
    events = collections.defaultdict(set)
    with open(LEGACY / "NRBOOK.csv", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter=";"):
            if r["BK_BKTYP"].strip() in EXIT_KINDS:
                events[r["BK_POLNR"].strip()].add(int(r["BK_EVTNR"]))
    return events


def readiness():
    """(passed, total) of the last readiness run (readiness.py writes lab/out/readiness_ours.txt)."""
    lines = (ROOT / "lab/out/readiness_ours.txt").read_text().splitlines()
    checks = [ln for ln in lines if ln.startswith(("PASS", "FAIL"))]
    return {"passed": sum(ln.startswith("PASS") for ln in checks), "total": len(checks),
            "checks": [ln.split(None, 1)[1].strip() for ln in checks]}


def milestones():
    """Score milestones transcribed from logs/*.md and git log (visuals/data/milestones.csv)."""
    with open(DATA / "milestones.csv", encoding="utf-8") as f:
        return [r for r in csv.DictReader(f)]


# ---------------------------------------------------------------- report/interactive.html: example policies

EXAMPLES = (  # (label, test on (first version, booking kind counts)); the first training policy that passes is used
    ("Started before the 2007 switch to Java (COBOL years)",
     lambda v, k: int(v["PH_BEGDT"]) < 1070811 and v["PH_FREQ"] == "M" and not k["SUR"] + k["DTH"]),
    ("Surrendered by the customer", lambda v, k: k["SUR"] > 0),
    ("Ended by the death of the insured person", lambda v, k: k["DTH"] > 0),
    ("Paid in Swiss francs (CHF)", lambda v, k: v["PH_CCY"].strip() == "CHF"),
    ("Paid in US dollars (USD)", lambda v, k: v["PH_CCY"].strip() == "USD"),
    ("Paid in British pounds (GBP)", lambda v, k: v["PH_CCY"].strip() == "GBP"),
    ("One single premium at the start", lambda v, k: v["PH_FREQ"] == "E"),
    ("Yearly premiums", lambda v, k: v["PH_FREQ"] == "J"),
    ("Many fund switches", lambda v, k: k["SWO"] >= 8),
)


def booking_kinds():
    """{policy: Counter of NRBOOK booking types} in one pass over the file."""
    kinds = collections.defaultdict(collections.Counter)
    with open(LEGACY / "NRBOOK.csv", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter=";"):
            kinds[r["BK_POLNR"].strip()][r["BK_BKTYP"].strip()] += 1
    return kinds


def examples():
    """Policy stories for the interactive page: the showcase policy plus one training policy per EXAMPLES label."""
    train = sorted(scoring.read_targets(str(TARGETS), "t2_projected_maturity_value"))
    first = {pid: min(v, key=lambda r: int(r["PH_VRSNR"])) for pid, v in grouped(L, "NRPOLH", "PH_POLNR").items()}
    kinds = booking_kinds()
    chosen = {POLICY: "€315 a month, with a premium holiday (the policy of the video)"}
    for label, test in EXAMPLES:
        pid = next((p for p in train if p not in chosen and test(first[p], kinds[p])), None)
        if pid:
            chosen[pid] = label
    target = scoring.read_targets(str(TARGETS), "t3_surrender_value")
    dates = sorted({d for _, d in target})
    found = {pid: b for pid, b in read_bookings(L) if pid in chosen}
    stories = []
    for pid, label in chosen.items():
        policy = contract(L, pid)
        rows = replay(policy, found[pid])
        stories.append({"label": label, **policy_story(pid, policy, rows, Account(policy, rows), dates)})
    return stories


# ---------------------------------------------------------------- 07, 09, 10: the loop, the scorecard, the rules

SEARCH_GRID = ("broker_date=current,first,PR_DUEDT,PR_RCVDT", "rate_date=PR_DUEDT,PR_RCVDT",
               "rounding=half_up,half_even,down")


def t0_search():
    """Step 3 of the loop: lab/search.py over the t0 choice points, timed (it writes lab/out/t0_commission_search.csv)."""
    import subprocess
    import time
    command = [sys.executable, str(ROOT / "lab/search.py"), "t0_commission", "--func",
               "variants.t0_commission:t0_commission", "--jobs", "8"]
    for grid in SEARCH_GRID:
        command += ["--grid", grid]
    start = time.time()
    subprocess.run(command, cwd=ROOT, check=True, capture_output=True)
    seconds = time.time() - start
    with open(ROOT / "lab/out/t0_commission_search.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    best = rows[0]
    return {"candidates": len(rows), "seconds": round(seconds, 1), "best": {k: best[k] for k in ("broker_date", "rounding")},
            "best_holdout": float(best["holdout"]), "best_wrong": int(best["wrong"])}


def t5_summary():
    """t5 flags on train, and how many of the old system's own list of corrections (NREXCP) they cover."""
    flagged = scoring.normalize_outliers(submission.t5_outlier_detection(L, str(TARGETS)))
    train = set(scoring.read_targets(str(TARGETS), "t2_projected_maturity_value"))
    hits = {(task, core.policy_of(key)) for task, key in flagged}
    listed = [(r["EX_TARGET"].split(".")[0], r["EX_POLNR"].strip()) for r in core.table(L, "NREXCP")
              if r["EX_POLNR"].strip() in train]
    return {"flagged": len(flagged), "listed_in_train": len(listed), "listed_found": sum(e in hits for e in listed)}


def rule_examples():
    """One real example per rule card (10_rules_found.png), from our engine and the data."""
    from neuron.calendar.holidays import EASTER_HOLIDAYS, FIXED_HOLIDAYS
    from neuron.cyymmdd import parts
    from neuron.terms.java_age import entry_age_java
    from neuron.terms.months_of_age import months_of_age
    commission = submission.t0_commission(L)[POLICY, 1]
    premium = next(p for p in core.table(L, "NRPREM") if p["PR_POLNR"].strip() == POLICY and p["PR_DUENR"] == "1")
    smoker_factor = {r["CG_SMKFAC"] for r in core.table(L, "NRCHRG")}
    smoke_codes = collections.Counter(r["PS_SMOKE"].strip() for r in core.table(L, "NRPERS"))
    floor_id, floor_day = "BL10001005", dt.date(2025, 12, 31)
    policy, rows, acc = one_policy(floor_id)
    floor = dict(surrender_values(floor_id, acc, [floor_day]))[floor_id, floor_day]
    age = None
    for pid in sorted(scoring.read_targets(str(TARGETS), "t2_projected_maturity_value")):
        p = contract(L, pid)
        if int(p.first["PH_APPDT"]) >= p.cobol_until:
            birth = parts(p.person["PS_BIRTH"])
            months = months_of_age(birth, p.start)
            if months % 12 >= 6:
                age = {"policy": pid, "birth": dt.date(*birth).isoformat(), "start": p.start.isoformat(),
                       "years": months // 12, "months": months % 12, "age": entry_age_java(birth, p.start)}
                break
    return {
        "commission": {"policy": POLICY, "premium": str(num_text(premium["PR_AMTRC"])), "commission": str(commission),
                       "rate": str(commission / num_text(premium["PR_AMTRC"]))},
        "smoker": {"codes": dict(smoke_codes), "factors": sorted(str(num_text(f, 6)) for f in smoker_factor)},
        "floor": {"policy": floor_id, "date": floor_day.isoformat(), "value": str(policy_value(acc, legacy(floor_day))),
                  "surrender": str(floor)},
        "age": age, "holiday_rules": len(FIXED_HOLIDAYS) + len(EASTER_HOLIDAYS),
        # BL10002262, run of 2019-12-01: N0013 and N0025 both 3013.17 before the risk charge; NRBOOK has an RSK row
        # only for N0025 (logs/t3-t4.md 2026-10-17 06:04, audit section 6)
        "tie": {"policy": "BL10002262", "date": "2019-12-01", "pots": ["N0013", "N0025"], "value": "3013.17",
                "winner": "N0025"},
    }


def num_text(text, scale=2):
    """Fixed-point text -> Decimal (N(2) by default)."""
    return Decimal(int(text)).scaleb(-scale)


def compute():
    """All numbers, as JSON-friendly values."""
    return {"policy": policy_life(), "t0": t0_discovery(), "era": system_change(), "calendar": calendar(),
            "scores": scores(), "exits": exits(), "readiness": readiness(), "milestones": milestones(), "examples": examples(),
            "search": t0_search(), "t5": t5_summary(), "rules": rule_examples()}


def load(reuse=False):
    """numbers.json, recalculated unless `reuse` and it exists."""
    path = DATA / "numbers.json"
    if not (reuse and path.exists()):
        DATA.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(compute(), indent=1))
    return json.loads(path.read_text())
