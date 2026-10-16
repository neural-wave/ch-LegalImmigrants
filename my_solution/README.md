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
| `market.py` | NRFPRC prices (latest publication, last price <= date), NRFXRT ratios, era rounding to cent / unit |
| `bookings.py` | streams NRBOOK policy by policy (6.8 M rows, never all in memory), drops reversed / 990 events |
| `premiums.py` | the blank PRM columns: invested amount, units and entry charge of a premium booking |
| `tariff.py` | parameters and formulas of a charge run: NRCHRG, agreed AMC, age / qx, AMC and risk formulas |
| `charges.py` | the monthly charge run: valuation, ADM -> AMC -> RSK, pro-rata splits, units sold |
| `accounting.py` | the replay in trade-date order; keeps holdings per date (t3) and amounts per year (t4) |
| `ages.py` | risk age: COBOL entry age + policy years, Java nearest birthday in whole months (t2, t3, t4) |
| `t0.py` .. `t4.py` | the rules of each task (module docstring = list of rules found) |

## Rules found so far

Train accuracy: t0 99.996 %, t1 100 %, t2 99.01 %, t3 96.05 %, t4 97.56 % (the train targets contain the
manual corrections of t5, so a perfect rule set scores slightly below 100 %). All five tasks run in about
40 s with a peak of 2.1 GB RAM.

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
management charge AMCP2/12, risk charge on the sum at risk (`qx/12 x (1 + loading) x smoker factor`), growth
at rate/12; each step rounded by the era of the application. **Risk age** (shared by t2 and the charge run,
`ages.risk_age`): offers applied for in the COBOL era use the entry age (nearest birthday from calendar
days / 365, impossible birth days clipped to the month end) plus the completed policy years, for their
whole life; Java offers use the nearest birthday in whole months at the anniversary.

**Fund accounting (t3, t4).** NRBOOK is replayed per policy in trade-date order (charge run before the
customer orders of the same day). Bookings of reversed (900) and 990 events do not count. PRM: amount =
premium x (1 - entry rate) x allocation share to the cent, units = amount x fx / ask price (fx of the day
before the trade date), parameters as of the money date. Charge run (one event, order ADM -> AMC -> RSK):
every fund/pot valued at units x bid / fx to the cent; the admin fee is split over all fund/pots pro rata by
value (largest absorbs the residual, 0.00 shares are not booked); AMC per pot, Java value x rate / 12 half up,
COBOL value x rate x days / 360 truncated (days since the previous run); the risk charge
`sum at risk x qx / 12 x (1 + loading) x smoker` on the value left after ADM and AMC, split like ADM.
Units sold = amount x fx / bid to 6 decimals. Every rounding follows the era of the trade date.

**t3 surrender value.** Policy value = sum over fund/pots of units x bid / fx on the valuation date, each
rounded to the cent in the era of the *valuation* date (2006-12-31 truncates). Penalty = NRSURR rate of the
product's scale by completed policy years since the start date, rounded half up, none in a NRWAIV period;
0 for policies in state 60/70 on the valuation date.

**t4 annual statement.** Years from the start year to the year of the first version in state 60/70, at the
latest 2025. Premiums = items in state P by money date; entry charges = premium x share - invested amount
of each PRM booking by its trade date; admin / management / risk = charge amounts by trade date;
total = entry + admin + management + risk.

**t5.** See `t5.py`.

## Team — Legal Immigrants

- Amar Omerovic
- Uzair Naeem
- Aanchal Aanchal
- Davide Frosi
- Fatih Tkin

All members worked together on data analysis, rule discovery, code and the write-up.

## AI tools

Claude Code (Anthropic) was used throughout: for the exploratory analysis that discovered the rules above
(hypothesis scripts checked against the train targets) and for generating and refactoring the submission
code. All rules were verified by the team against the train targets with `check.py`.
