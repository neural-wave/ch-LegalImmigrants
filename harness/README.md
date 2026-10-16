# harness: the rule-finding tool

Generic tooling to find the hidden rules of a task of the Neuron migration challenge (see the opening briefing,
section 4 of `brief.md`). It is **not part of the submission**: it reads the target files, which submitted code must
never do. It works for any task t0-t4 because it only relies on `scoring.py` and the legacy tables.

| Module | What it does |
|---|---|
| `evaluate.py` | `evaluate(task, predictions, targets_dir)` scores exactly like `scoring.py` and returns a `Mismatches`: one row per target with `predicted`, `target`, `diff` (cents or days), `match`, joined with the policy features. NREXCP manual corrections are left out like in the official evaluation (`exclude_manual=False` to keep them). |
| `features.py` | per-policy features from the legacy tables (application/start date, tariff family/generation/premium type/death option, product, currency, broker tier, frequency, payment method, state, insured age at start, sex, smoker, mortality table, era) and the row-level date of keyed tasks (due date, valuation date, year). |
| `explain.py` | `explain(mm)`: accuracy, diff histogram, where the mismatches concentrate, groups with a high mismatch rate, a depth-3 decision tree printed as rules with support, change points of the mismatch rate over time (ruptures Pelt + best single split), the era-boundary check, the worst rows. |
| `search.py` | `search(task, build_fn, space)`: greedy coordinate search over named rule variants; configs are plain dicts, so a new idea is one more entry in `space`. Logs every trial. |
| `report.py` | saves `report.md`, `mismatches.csv` and PNGs (mismatch rate by application date / row date, diff histogram) in `reports/<task>/`. |
| `cli.py` | command line, see below. |
| `demo_t2.py`, `demo_search_t2.py` | demos on t2 with the exploration rules of `analiza/t2_recon.py`. |

## Usage

From `repo/` with the project interpreter:

```
python -m harness.cli evaluate t2 --submission ../my_solution --legacy ../../data/legacy --targets ../../data/targets
python -m harness.cli evaluate t0 --predictions harness/reports/t0/predictions.csv   # a target-shaped CSV instead
python -m harness.demo_t2             # t2 with the t2_recon rules -> reports/t2/
python -m harness.demo_search_t2      # hill-climb from a wrong configuration to the known rules
```

In Python:

```python
from harness import evaluate, explain, search
mm = evaluate("t2", my_solution.t2_projected_maturity_value(legacy_dir), targets_dir)
findings = explain(mm)          # dict with rules, change points, histogram ... (also printed)
mm.mismatches                   # DataFrame of the failing rows with all features
result = search("t2", build_fn, {"rounding": ["era", "half_up", "truncate"], "monthly_rate": ["r_over_12", "geometric"]})
```

Reading the output: the **tree** and the **concentration** section answer *what* the mismatches have in common
(tariff, table, age ...), the **change points** answer *when* they start; the two together usually name the missing
rule. The **era-boundary check** says whether the COBOL/Java switch of 2007-08 still explains anything.
