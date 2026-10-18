# Readiness tests

The same 29 checks for any solution of the Neuron challenge. They test what the hidden evaluation might throw at a
solution beyond the training data. Nothing here is tuned to one solution.

## Run

```
python tests/readiness.py <solution folder> <participants folder> [name]
```

- `<solution folder>`: the folder with `submission.py` (e.g. `my_solution`).
- `<participants folder>`: the unzipped challenge folder with `legacy/`, `targets/` and `starter_kit/scoring.py`.
- Python 3.10+, standard library only. A full run takes about 15 minutes (20 complete runs of all tasks).

It prints one line, e.g. `my_solution: readiness 29/29 checks passed`, and writes every check with PASS or FAIL to
`tests/out/readiness_<name>.txt`.

## The checks

| Group | Checks | What it means |
|---|---|---|
| Real export | 1 | every task runs without an error |
| Train scores | 5 | each task scores above 99% with Lifeware's own `scoring.py` |
| Budget | 2 | the whole run takes under 120 s and under 4 GB of memory |
| Invariants | 1 | no negative surrender value, statement totals add up, no collection before its due date |
| Other inputs | 2 | it runs with extract date 2027-06-30 and other valuation dates, and t1 dates stay inside that window |
| Incomplete export | 18 | one data row is removed from a table the tasks read (2 random rows each from NRBROK, NRPERS, NRRISK, NRALLO, NRPREM, NRFPRC, NRFXRT, NRAGRE, NRPOLH; fixed seed 2026, so every solution gets the same rows) and every task must still run |

Why the incomplete-export checks: a legacy export can miss a row. If one missing row stops a task, the whole task
scores 0, not just the policy with the gap. A solution passes if it leaves out the affected policy and carries on.
