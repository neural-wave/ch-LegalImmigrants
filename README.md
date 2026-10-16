# Neuron Detective — The Neuron Migration (Lifeware), Neural Wave 2026

Team **Legal Immigrants**: Amar Omerovic, Uzair Naeem, Aanchal Aanchal, Davide Frosi, Fatih Tkin.

Neuron is a 30-year-old life-insurance administration system (COBOL until August 2007, Java since) whose
calculation rules were never written down. From its data export alone we reconstruct, to the cent and to the
day, the broker commissions (t0), the next premium due dates (t1), the projected maturity value of every offer
(t2), the surrender value on three valuation dates with the full fund accounting behind it (t3), the annual
statements (t4) and the values that were corrected by hand (t5). The rules are written as short, auditable
Python, found with a generic rule-finding tool (`harness/`).

## Results on the train policies

| Task | Exactly correct rows | What is left |
|---|---|---|
| t0 commission | 225 848 / 225 858 (99.996 %) | 10 manual corrections |
| t1 next due dates | 15 028 / 15 028 (100 %) | — |
| t2 projected maturity value | 3 011 / 3 019 (99.74 %) | 8 manual corrections |
| t3 surrender value | 6 131 / 6 153 (99.64 %) | 17 manual corrections, 5 one-cent splits |
| t4 annual statement | 34 118 / 34 145 (99.92 %) | 24 manual corrections, 3 one-cent splits |

The train targets still contain the manually corrected values (task t5), so a perfect rule set scores a
little below 100 % locally. All five tasks run in about 40 s with 2.1 GB of RAM; maintainability index
(radon, weighted by lines of code) 75.0. The rules themselves are documented in
[`my_solution/README.md`](my_solution/README.md) and in the module docstrings.

## Repository layout

| Path | Content |
|---|---|
| `my_solution/` | **the submission**: `submission.py` (one entry point per task) and one small module per concern (`loader`, `dates`, `params`, `market`, `bookings`, `premiums`, `tariff`, `charges`, `accounting`, `ages`, `t0` … `t5`). Standard library only, never reads `targets/`. |
| `check.py`, `scoring.py` | the organisers' local scorer and the official scoring, unchanged |
| `harness/` | our rule-finding tool: evaluate a candidate rule → explain the mismatches (features, decision tree, change points, era check) → search over rule variants; `harness/reports/` holds the generated reports and charts for t0 and t2 |
| `requirements.txt` | packages of the tool; the submission itself needs none |

The partner's data export (`legacy/`, `targets/`) is not in this repository.

## How to run

Python 3.12. The submission needs nothing beyond the standard library; the tool and the maintainability
check need `pip install -r requirements.txt`.

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

# score the submission against the train targets (same scoring as the evaluation)
python check.py --submission my_solution --legacy <path>/legacy --targets <path>/targets
python check.py --submission my_solution --tasks t3_surrender_value --legacy <path>/legacy --targets <path>/targets

# the rule-finding tool: score, explain and report the mismatches of one task
python -m harness.cli evaluate t2 --submission my_solution --legacy <path>/legacy --targets <path>/targets
```

Calling the submission directly:

```python
import datetime as dt, sys
sys.path.insert(0, "my_solution")
import submission
submission.t2_projected_maturity_value("<path>/legacy")                   # {policy_id: Decimal}
submission.t3_surrender_value("<path>/legacy", [dt.date(2025, 12, 31)])   # {(policy_id, date): Decimal}
```

## Approach in short

1. **Measure first.** Every candidate rule is scored with the official `scoring.py`; the harness joins the
   failing rows with the policy features (dates, tariff, generation, broker tier, currency, age, …), prints a
   shallow decision tree over them and looks for change points in time. Tree + change point usually name the
   missing condition (e.g. "tariff generation 01/02", "before August 2007").
2. **Two systems, one export.** The conversion event of 2007-08-11 splits every rule in two: COBOL truncates
   to the cent and drifts due dates, Java rounds half up and anchors them. Which era applies depends on the
   date of the thing being computed (booking, valuation, application).
3. **Step by step through the diagnostics.** t3 was built booking by booking against `t3_booking` /
   `t3_holding` (premium investments, then admin, management and risk charges, then valuation), never
   against the final value alone.
4. **Short modules.** One concern per file, docstrings that list the rules found, no tables of values.

## AI tools

Claude Code (Anthropic) was used throughout: to write and run the exploration scripts that tested
hypotheses against the train targets, to generate and refactor the submission code and the harness, and to
draft this documentation. Every rule in the submission was verified by the team with `check.py` on the train
targets; the diagnostics-driven search described above is the team's method, executed with the assistant.

## Report and video

- Report (max. 3 pages): `report/` — added before the deadline.
- 2-minute video: link provided to the organisers via Swisstransfer.

## License

MIT, see `LICENSE`. The challenge material (`check.py`, `scoring.py`, `SCHEMA.md`) belongs to Lifeware.
