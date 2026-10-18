# 5-minute talk: outline

Eight slides, about 35 seconds each. One idea per slide, with big numbers and few words. The figures are in
`visuals/out/` (each GIF also has a still `.png` if the slides can't play GIFs). Keep a terminal open for the demo on
slide 7.

## 1. Thirty years and no source code (0:00–0:30)
- Visual: `01_policy_life.gif`
- An insurer in Ticino has run every policy on Neuron since 1994, first in COBOL and later in Java.
- Neuron is being switched off and nobody knows its formulas any more. We got its data and some of its answers.
- The new system has to give the same answers **to the cent and to the day**. If it's a cent off, someone has to
  investigate.

## 2. Six tasks, one method (0:30–1:05)
- The tasks are commission, due dates, the offer value at maturity, the surrender value, the annual statement, and
  finding hand edits.
- Example: policy BL10000013 pays €315 a month. Its broker is in tier B and earns 3%, so €9.45.
- We handle every task the same way. What is one row, which rows count, what is the formula? Then we test the
  **choice points**: which date, which rounding, which version of the policy.

## 3. The lab and the factory (1:05–1:40)
- Visual: `07_architecture.png`
- **The lab** finds rules: a diff tool, a decision tree on the wrong rows, and a search over choice points that we
  check on 20% of the policies we never tune on.
- **The factory** is what we hand in. It's plain Python with the standard library, money as `Decimal` and every rate
  looked up by date. There's no machine learning and no AI call in it.
- The AI helps us find the rules. Plain code does the sums, so an auditor can read every one.

## 4. How we found one rule (1:40–2:15)
- Visual: `03_rule_discovery.gif`
- We first used each policy's current broker for the commission. 1,440 rows were wrong.
- The decision tree showed that 1,430 of them were on policies whose broker had changed tier. The search then tried
  24 combinations in 8 seconds.
- The best was the broker on the day the money arrived. 10 rows were left, and 6 of them are on Neuron's own list of
  corrections.

## 5. Rules hidden in the history (2:15–2:55)
- Visuals: `04_system_change.png`, `06_calendar.png`
- On 11 August 2007 Neuron moved from COBOL to Java. COBOL **cuts off** cents (12.349 → 12.34). Java **rounds**
  (12.35).
- COBOL also charged the management fee by days (divided by 360) and counted age in 365-day years.
- Direct debits follow the 15 public holidays of canton Ticino. Corpus Christi is one of them. Good Friday isn't.
- The invisible pot: a €1.88 leftover with no booking row still counts when the admin fee is shared out.

## 6. Results (2:55–3:35)
- Visual: `02_score_climb.gif`, then the results table
- Train scores: t0 99.9956%, t1 100%, t2 99.735%, t3 99.74%, t4 99.9414%.
- 54 rows are left, exactly the 54 that t5 flags. 38 are on Neuron's own correction list. The other 16 move by whole
  euros too, so we think they are unlisted hand edits.
- The official scoring leaves hand edits out, so our estimate is **100% on every task**.
- All 5,024,847 fund bookings match. Code quality is 100.0, and all six tasks run in 40 seconds.

## 7. Does it work on new data? (3:35–4:20)
- Visual: `08_unseen_proof.png`
- 286 public policies, with no answers given to us, were cashed in or ended by death. If one charge were wrong, units
  would be left over. Our replay ends **every one at exactly 0**.
- On the 20% of policies we never tuned on, the scores match the rest once hand edits are left out. The code has no
  fitted numbers and no policy ids.
- Our readiness suite passes 29 of 29 checks, including 18 exports with one row deleted. A broken policy is skipped,
  and the task still runs.
- Live demo (20 s): `./check.sh --tasks t1_next_due_dates` shows 100%.

## 8. How we worked (4:20–5:00)
- We worked utilizing agentic AI. Several AI agents worked in parallel on separate tasks, and one coordinating agent
  re-ran every score before accepting it. We directed the work, approved each change and reviewed the code.
- Every attempt and every failed idea is written down in `logs/`. Two we liked: the smoker flag is `J` for "Ja", not
  `Y`, and a "fair" way to split fees broke about 80% of the policies.
- For a new target, the lab tools work as they are. You point them at the new file and start looking at wrong rows.
- Close with the results table on screen and thank the jury.

## Likely questions
- **Why not use machine learning for the values?** It can't be exact to the cent, and an auditor can't check it. We
  only use it to find where our rules break.
- **How do you know the 54 are hand edits and not missing rules?** 38 are on Neuron's own list. We can't prove the
  other 16. They look the same, though: they move by whole euros while every related value (the year values, the
  policy value, the other columns) is exact. A missing rule would leave odd cents.
- **What if the private data is messier?** A policy with missing data is skipped, and the task goes on. We tested 18
  broken exports, and an export twice as big ran in 88 s.
- **Is the code quality score real?** Radon gives 100 to files without arithmetic operators, so you could get it by
  hiding them. We didn't. Each module holds one short rule with a docstring that says why.
