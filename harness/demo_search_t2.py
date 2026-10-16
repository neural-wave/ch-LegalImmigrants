"""Demo of `harness.search` on t2: hill-climb from a deliberately wrong configuration to the known rules.

Each dimension is a plain name; `to_cfg` translates it into the knobs of analiza/t2_recon.py. Run from repo/:

    .venv/bin/python -m harness.demo_search_t2
"""
import contextlib
import sys

from harness import paths
from harness.search import search

sys.path.insert(0, str(paths.LIFEWARE / "analiza"))
import t2_recon as t  # noqa: E402

SPACE = {
    "rounding": ["half_up", "truncate", "era"],  # era = truncate before the COBOL->Java switch, half-up after
    "monthly_rate": ["geometric", "r_over_12"],
    "param_date": ["begdt", "appdt"],
    "risk_age": ["floor", "nearest"],
}
START = {"rounding": "half_up", "monthly_rate": "geometric", "param_date": "begdt", "risk_age": "floor"}


def to_cfg(config):
    cfg = dict(t.CFG, auto=False, rv="hu", rc="hu", rp="hu")
    if config["rounding"] == "truncate":
        cfg.update(rv="dn", rc="dn", rp="dn")
    elif config["rounding"] == "era":
        cfg.update(auto=True)
    cfg["mrate"] = "geo" if config["monthly_rate"] == "geometric" else "lin"
    cfg["pdate"] = cfg["rdate"] = "app" if config["param_date"] == "appdt" else "beg"
    cfg["age"] = config["risk_age"]
    return cfg


def build(config):
    cfg = to_cfg(config)
    out = {}
    for policy in t.first.index:
        try:
            out[policy] = t.r2(t.project(policy, cfg)[0])
        except Exception:  # noqa: BLE001
            pass
    return out


if __name__ == "__main__":
    result = search("t2", build, SPACE, start=START)
    print("\nbest:", result.best, f"{result.correct}/{result.total} = {result.accuracy:.4%}")
    result.log()
    out = paths.REPORTS / "t2" / "search_log.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f, contextlib.redirect_stdout(f):
        print("greedy coordinate search on t2, start =", START, "\nspace =", SPACE, "\n")
        result.log()
        print("\nbest:", result.best, f"{result.correct}/{result.total} = {result.accuracy:.4%}")
    print("log saved to", out)
