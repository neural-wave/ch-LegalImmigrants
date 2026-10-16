# Neuron Detective — Lifeware challenge, Neural Wave 2026

Team **Legal Immigrants**. Reverse-engineering the rules of a 30-year-old life-insurance administration system
("Neuron") from its data export, and writing them down as short, auditable Python.

- `my_solution/` — the submission: `submission.py` (entry points per task) and one small module per concern.
  Details, rules found and team members: [`my_solution/README.md`](my_solution/README.md).
- `check.py`, `scoring.py` — the organisers' local scorer (`python check.py --submission my_solution --legacy <legacy_dir> --targets <targets_dir>`).
- `harness/` — our rule-finding tool (evaluate → explain mismatches → search variants). Not part of the scored submission.

The partner's data export is not in this repository.
