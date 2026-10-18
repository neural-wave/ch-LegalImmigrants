# my_solution: approach and rules

`submission.py` only re-exports the six task functions. Each task is one module in `tasks/`. The shared engine is in
`neuron/`, with one small module per rule. Each module's docstring says why the rule works the way it does.

Every value is calculated from `legacy_dir`. Only t5 reads `targets_dir`, as the challenge allows. There are no
dependencies. The code runs on the Python 3.10+ standard library, so `requirements.txt` is empty on purpose.

## Approach in short

For each task we decided what one row is, which rows count and what the formula is. Then we tested the choice
points: which date, which rounding, which version of the policy. We found the rules offline with the tools in `lab/`
at the repo root (a diff tool, a decision tree on the wrong rows, and a search over choice points that is checked on
a 20% hold-out). A rule only moved into this folder once it was short, readable and proven on the data. The code here
has no machine learning, no AI calls and no target values.

The whole engine follows three habits.

- **Money is `Decimal`**, never a float. Fixed-point columns are decoded once (`neuron/fixed_point.py`).
- **Every rate comes from a parameter table by date.** `as_of(rows, prefix, day)` picks the row valid on that day,
  highest version first (`neuron/as_of.py`). For example, the admin fee is 6.50 until 2022 and 8.00 from 2023.
- **Two eras.** Each policy's event 800 (11 August 2007) marks the switch from COBOL to Java Neuron
  (`neuron/contract.py`). COBOL cuts off cents and units (12.349 → 12.34), and Java rounds half up (12.35). This is the
  only date where the rules change.

`guarded()` (`neuron/data.py`) skips a policy with incomplete data, so one broken row never stops a whole task.

## Rules per task

### t0 Commission (`tasks/t0_commission.py`)
1. Only premium items with state `P` (paid) earn a commission.
2. Commission = premium received × rate, rounded half up to the cent. Example: BL10000013 pays €315, its broker is in
   tier B, the regular-premium rate is 3%, so €9.45.
3. The rate is looked up by the tier of the broker in the policy version valid on the **money date** (`PR_RCVDT`),
   and by `E` for single-premium policies, `L` for the others.

### t1 Next due dates (`tasks/t1_next_due_dates.py`, `neuron/calendar/`)
1. Policies in state 10 with a regular frequency (M, Q, H, J), in the version valid on the extract date.
2. Step from the start date: M 1, Q 3, H 6, J 12 months. No due date on or after maturity.
3. COBOL era: next due = last due + step, clamped to the month end, so the day "sticks" (31 Jan → 28 Feb → 28 Mar).
   Java era: the day of the first due date after the conversion is kept for good (clamped per month only).
4. Collection: bank transfer (UB) = due date, even on a weekend. Direct debit (LS) = next business day.
5. Business days: Monday–Friday minus canton Ticino's 15 public holidays: 1 and 6 Jan, 19 Mar, Easter Monday, 1 May,
   Ascension, Whit Monday, Corpus Christi, 29 Jun, 1 and 15 Aug, 1 Nov, 8, 25 and 26 Dec. **No Good Friday.** The
   same calendar for every currency. Easter is computed (`neuron/calendar/easter.py`), so it works for any year.

### t2 Projected maturity value (`tasks/t2_projected_maturity_value.py`, `neuron/offer/`)
1. The offer treats the policy as one amount, simulated month by month from the start to the maturity date, with all parameters as of the
   **application date** and the first policy version.
2. Each month: + premium × (1 − entry rate) on premium months → − admin fee → − value × management rate / 12 →
   − risk charge → × (1 + growth rate / 12). Every step is rounded to the cent (cut off in the COBOL era).
3. Growth is r / 12 per month, not (1 + r)^(1/12). The management rate is the base-unit rate `CG_AMCP2`.
4. Risk = sum at risk × qx(age) × (1 + loading) × smoker factor (only if `PS_SMOKE = J`) / 12. Sum at risk by death
   benefit option: A 1% of the value, B max(sum insured − value, 0), C the sum insured.
5. Age = entry age + completed policy years. Java entry age: nearest birthday in whole months
   ((months + 6) // 12). COBOL entry age: round(days since birth / 365).
6. Some birth dates don't exist (1954-11-31). They are kept as numbers, never turned into a date.

### t3 Surrender value (`tasks/t3_surrender_value.py`, `neuron/funds/`)
1. Replay `NRBOOK` per policy, one trade (one event on one trade date) at a time, sorted by trade date with **the
   monthly charge run first on its day**. Reversed events and technical corrections (990) are skipped. Customer
   orders (switches, withdrawals, surrenders, deaths) keep their exported units.
2. Premium: amount per fund = round(premium × (1 − entry rate) × allocation share), with the rates and allocation of
   the money date. Units = amount × FX / ask price. The FX is the rate of the **day before the trade date**.
3. FX = CHF rate of the policy currency / CHF rate of the fund currency, never rounded. Currency codes are upper-cased
   (`usd` appears in the table).
4. Charge run: the value of every pot the policy holds (also those without a booking row) at the bid price. Admin fee
   = min(fee, value), shared by value: each share rounded, the largest pot takes the remainder. Management charge per
   pot = value × rate × period: Java 1/12, COBOL days since the previous monthly anniversary / 360 (Act/360).
   Risk charge on the value left after admin and management, at most that value.
5. Risk charge as in t2, with the age at the last policy anniversary (a 29 Feb start has its anniversary on 28 Feb).
6. Surrender value = Σ per pot cents(units × last bid / FX) × (1 − surrender penalty of the completed policy years),
   with no penalty inside a waiver period (`NRWAIV`). The value is 0 for surrendered or dead policies (state 60/70)
   and never below 0.

### t4 Annual statement (`tasks/t4_annual_statement.py`)
1. The same replay as t3 (run once and shared).
2. Premiums by money date. Entry charges per fund in the year of that fund's trade date (a premium paid on 30 Dec can
   trade one fund on 31 Dec and another on 2 Jan). Admin, management and risk charges by trade date.
3. Years from the start year to the year of state 60/70, at most 2025. Total = entry + admin + management + risk.

### t5 Hand edits (`tasks/t5_outlier_detection.py`)
1. Our working rule: a manual correction moves one value by a **whole, non-zero amount**, while a missing rule
   leaves odd cents.
2. t0 and t2: compare the target with our task function. t3: compare the target surrender value with the target
   policy value after the penalty. t4: compare the target admin fees with the tariff fee × the charge runs of the year.
3. On train this flags 54 rows. 38 are all the `NREXCP` entries that have train targets. The other 16 are not listed
   but move by whole euros in the same way, so we believe they are unlisted edits.

## Results on train (official `check.py`)

| Task | Raw score | Estimated, hand edits excluded |
|---|---|---|
| t0 | 99.9956% (225,848 / 225,858) | 100% |
| t1 | 100% (15,028 / 15,028) | 100% |
| t2 | 99.735% (3,011 / 3,019) | 100% |
| t3 | 99.74% (6,137 / 6,153) | 100% |
| t4 | 99.9414% (34,125 / 34,145) | 100% |
| t5 | 54 flagged | |

Maintainability index 100.0 on all 99 files. All six tasks run in 40 s.
