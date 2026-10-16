# Neuron migration challenge - submission

Reconstruction of the undocumented calculation rules of Neuron, the legacy policy administration system of
NeuralWave Life, from its data extract (`legacy/`). Pure Python 3.12 standard library: amounts are
`decimal.Decimal`, dates are `datetime.date`, nothing is cached on disk and `targets/` is never read.

## How to run

```bash
python check.py --submission my_solution --legacy ../data/legacy --targets ../data/targets
# only some tasks:
python check.py --submission my_solution --tasks t0_commission t1_next_due_dates t2_projected_maturity_value
```

`requirements.txt` is empty on purpose; `pip install radon` is only needed to print the maintainability index.

## Layout

| File | Content |
|---|---|
| `submission.py` | the entry points `t0_...` to `t5_...`, one line each, delegating to the task modules |
| `loader.py` | cached `csv.DictReader` over the legacy tables, trimmed fields, `N(s)` -> `Decimal` |
| `dates.py` | `CYYMMDD` decoding, month arithmetic with an anchor day, COBOL/Java era, Ticino business days |
| `params.py` | "as of date" lookups: policy versions, NRCHRG, NRENTC, NRCOMR, NRILLU, NRAGRE, NRALLO |
| `t0.py`, `t1.py`, `t2.py` | the rules of each task (module docstring = list of rules found) |

## Rules found so far

Train accuracy: t0 99.996 %, t1 100 %, t2 99.01 % (the train targets contain the manual corrections of t5,
so a perfect rule set scores slightly below 100 %).

**Era split.** Neuron was converted from COBOL to Java on the weekend of 2007-08-11/12 (event type 800,
dated 2007-08-11). The COBOL era (up to 2007-08-10) truncates amounts to the cent, the Java era rounds half up.

**t0 commission.** `amount received x rate(broker tier, premium type)`, rounded half up to the cent. The
broker comes from the policy version valid on the money received date, the premium type (L/E) from position 6
of the tariff key. Items without money and items whose booking event was reversed (event type 900) are not
counted.

**t1 next due dates.** Version valid on the extract date, state 10, frequency M/Q/H/J. Due dates are
start date + k x frequency months with the day clamped to the month length; COBOL-era policies keep the day
of their last pre-conversion due date as anchor. Horizon: one year after the extract date, before maturity.
Direct debit (LS) collects on the next Ticino business day, other methods on the due date.

**t2 projected maturity value.** Replay of the offer projection with the parameters valid on the
application date of version 1 (charges by tariff family/generation, entry charge by broker tier,
illustration rate; no individual agreements). Monthly loop: premium net of entry charge, admin fee,
management charge AMCP2/12, risk charge on the sum at risk (`qx/12 x (1 + loading) x smoker factor`, age at
the anniversary to the nearest birthday), growth at rate/12; each step rounded by the era of the application.

**t3, t4, t5.** Not yet implemented (return empty results).

## Team

- Full name 1 (placeholder)
- Full name 2 (placeholder)
- Full name 3 (placeholder)

## AI tools

Claude Code (Anthropic) was used throughout: for the exploratory analysis that discovered the rules above
(hypothesis scripts checked against the train targets) and for generating and refactoring the submission
code. All rules were verified by the team against the train targets with `check.py`.
