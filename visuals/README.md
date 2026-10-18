# Visuals (task t6, report and video)

Ten visuals, each with one message. Every number in them is calculated by our engine (`my_solution/neuron`,
`tasks/`) or the lab tools (`lab/`) from the challenge data. The only exception is the score history in 02, which
is copied from the team logs and git history, with one source per row in `data/milestones.csv`.

Regenerate everything (from the project root, about 2 minutes):

```bash
.venv/bin/python visuals/make_all.py
```

`--reuse` redraws from the saved numbers in `data/numbers.json` in seconds. `--only 01 05` draws a few.
GIFs are 1280 × 720 at 10 frames per second and loop; PNGs are 1920 × 1080. Each GIF also has a settled PNG still
(`out/01_policy_life.png`, `out/02_score_climb.png`, `out/03_rule_discovery.png`) for the report.

**One theme for everything.** `theme.json` holds the colours, fonts, text sizes, layout and motion timing;
`theme.css` has the same tokens for HTML and PDF. `style.py` reads `theme.json`, so the charts, the report, the
interactive page and the video share one look.

**Animation rules.** Every GIF is a series of steps: a move of at most 0.5 s, then the step holds, fully settled,
for 2–2.5 s (the last one 3.5 s). Headings and numbers are only drawn once a step is settled, and no text sits on data.

**Interactive page.** `report/interactive.html` (made by `v11_interactive.py` from `interactive_template.html`) has
one tab per topic: score climb, one policy's life (10 example policies), annual statement by year, calendar,
finding a rule, unseen data. Plotly comes from a pinned CDN build; the data is embedded.

| File | Caption |
|---|---|
| `out/01_policy_life.gif` | One policy's life, month by month: each €315 premium buys fund units, monthly charges sell a few back, and the surrender value lands exactly on the target (€11,211.19 in April 2020, €31,111.18 in December 2025). |
| `out/02_score_climb.gif` | From first try to every rule found in one night: accuracy of t0–t4 rises to 100% (estimated: hand-edited rows left out, as the official scoring does), and the code readability score rises from 75.7 to 100. |
| `out/03_rule_discovery.gif` | How a rule is found: the simple guess gets 1,440 commissions wrong, a decision tree sees that 99% of them are on policies whose broker changed, and using the broker on the day the money arrived leaves only 10 hand edits. |
| `out/04_system_change.png` | In 2007 Neuron moved from COBOL to Java and the maths changed: old rules fail on every new offer, new rules fail on every old one, and our rule switches on 11 August 2007 and gets both right. |
| `out/05_statement_waterfall.png` | Where a year of premiums goes: the 2021 statement of one policy, €2,835 paid minus €439.47 of entry, admin, management and risk charges, every one exact to the cent. |
| `out/06_calendar.png` | Due on a holiday? The direct debit waits for the next business day: a year of due dates and collection dates, with weekends and the holidays of canton Ticino. |
| `out/07_architecture.png` | Our approach as a loop, on the real commission rule: compare with Neuron (1,440 rows wrong), find the pattern (98.8% paid before the broker changed), test 24 candidate rules on a held-back 20%, keep the plain rule (10 hand edits left); the factory hands in plain Python and its answers feed the next loop. |
| `out/08_unseen_proof.png` | Not fitted to the answers: on all 286 unseen policies that ended (and all 886 training ones), exactly 0 fund units are left after the surrender or death; the same accuracy on a 20% check group; 29 of 29 readiness checks pass. |
| `out/09_results_card.png` | The scorecard: every task at 100% estimated (raw train scores 99.9956 / 100 / 99.735 / 99.74 / 99.9414), code readability 100.0, 40 s runtime, 29/29 readiness checks, and 54 hand edits flagged (38 on the official list + 16 that look the same). |
| `out/10_rules_found.png` | Eight rules we found in the old system's data, each with a real example: the broker on the money date, COBOL vs Java rounding, days / 360, nearest-birthday age, Ticino business days, no negative surrender value, the tie-break cent, and the smoker flag "J". |

## Files

- `make_all.py`: runs everything. `data.py`: calculates every number. `style.py`: shared look (palette, fonts, GIF writer).
- `v01_*.py` … `v08_*.py`: one drawing per visual. `v11_interactive.py`: the interactive page.
- `theme.json`, `theme.css`: the shared design tokens.
- `data/numbers.json`: all numbers shown, so the report can quote them exactly. `data/milestones.csv`: score history with sources.

## Where the numbers come from

| Visual | Source |
|---|---|
| 01, 05 | BL10000013 replayed alone with the t3/t4 engine (`neuron/funds/replay.py`), valued with `tasks/t3_surrender_value.py`, statement from `tasks/t4_annual_statement.py` |
| 02 | `data/milestones.csv` (logs and git), final scores checked against the current code |
| 03 | `lab/core.py` diff frames of `lab/variants/t0_commission.py` (broker of today) and the shipped t0; depth-1 decision tree as in `lab/miner.py`, fit on the 80% split |
| 04 | t2 run three times with the conversion date moved (all Java, all COBOL, ours), compared with the train targets |
| 06 | t1 on the extract date 2026-06-30 for all policies; holidays from `neuron/calendar/holidays.py` |
| 07 | t0 diff frames (as 03), `lab/search.py` run and timed over 24 combinations (`data.t0_search`) |
| 09 | `data/numbers.json` scores, readiness, last MI milestone; t5 flags vs NREXCP (`data.t5_summary`) |
| 10 | `data.rule_examples` (t0 output, NRPERS, NRCHRG, BL10001005 replay, entry ages), the t1 calendar and the t2 era test; the 29-day and tie examples are from logs/t3-t4.md |
| 08 | SUR/DTH bookings in NRBOOK and the replayed units; scores per `lab/core.py` holdout split; `lab/out/readiness_ours.txt` from `readiness.py` |
