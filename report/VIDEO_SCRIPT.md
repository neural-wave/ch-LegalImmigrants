# 2-minute video: storyboard

Six scenes, 2:00 in total, with about 265 spoken words (around 130 words a minute). Use one voice, and no music
under the words or only very quiet music. The figures are in `visuals/out/`, and the demo recording is
`video/demo.mov`. Captions are short and stay on screen for the whole scene, so the video also works without sound.

| # | Time | Length | Visual | Caption on screen |
|---|---|---|---|---|
| 1 | 0:00–0:17 | 17 s | `01_policy_life.gif` | **30 years of rules. No source code.** |
| 2 | 0:17–0:35 | 18 s | `07_architecture.png` | **The lab finds the rules. The factory runs them.** |
| 3 | 0:35–0:53 | 18 s | `03_rule_discovery.gif` | **1,440 wrong rows → 10** |
| 4 | 0:53–1:11 | 18 s | `04_system_change.png`, then `06_calendar.png` | **2007: COBOL cuts off, Java rounds** / **Ticino holidays move direct debits** |
| 5 | 1:11–1:26 | 15 s | **demo:** `video/demo.mov` | **Lifeware's own scorer, running our code** / **A rule in plain Python** |
| 6 | 1:26–2:00 | 34 s | `02_score_climb.gif`, then `08_unseen_proof.png`, then the results card | **54 rows left: 38 on the official correction list, 16 more that look the same** / **It works on data it has never seen** |

## Scene 1 · 0:00–0:17 · The problem

**Visual:** `01_policy_life.gif`, the life of one policy, with premiums going in, charges coming out and the value
moving.

**Narration (41 words):**
> Since 1994, an insurer in Ticino has run its policies on a system called Neuron. Now Neuron is being switched off,
> and nobody knows its formulas. We only have its data, and the new system must match it to the cent.

## Scene 2 · 0:17–0:35 · The approach

**Visual:** `07_architecture.png`. Show the lab half first, then the factory half.

**Narration (43 words):**
> We split the work in two. The lab finds the rules. We built it utilizing agentic AI, with several agents working in
> parallel and one checking every result. The factory is the code we hand in. It's plain Python, with no AI inside.

## Scene 3 · 0:35–0:53 · How we found one rule

**Visual:** `03_rule_discovery.gif`, where the wrong rows shrink as the rule gets better.

**Narration (42 words):**
> Take the broker's commission. Using today's broker got 1,440 rows wrong. A decision tree showed that nearly all of
> them had changed broker. Then a search tried 24 versions in eight seconds. Neuron uses the broker on the day the
> money arrived.

## Scene 4 · 0:53–1:11 · Rules hidden in the history

**Visual:** `04_system_change.png` for the first 9 seconds, then `06_calendar.png`.

**Narration (40 words):**
> Other rules hide in the history. Until 2007 Neuron ran on COBOL, which cut off extra cents and counted days. Java
> rounds instead. Even the calendar is local. Direct debits skip Ticino's holidays, like Corpus Christi, but not Good
> Friday.

## Scene 5 · 1:11–1:26 · Demo: it really runs

**Visual:** the screen recording `video/demo.mov`, cut to 15 seconds.

- **0–9 s:** the terminal runs Lifeware's scorer on our submission: `./check.sh | grep -v "^  "`. The real run takes
  about 45 seconds, so show the command being typed, then speed up the wait (with a small "sped up" label in the
  corner) and hold on the output for 5 seconds. It shows one line per task with its score and time, t5 with
  54 outliers, and `maintainability index: 100.0`.
- **9–15 s:** `head -40 LifewareChallenge/participants/starter_kit/my_solution/tasks/t0_commission.py`. Hold on the
  docstring and `item_commission`, and highlight `PR_RCVDT`, the money date from scene 3.

**Narration (32 words):**
> Here is Lifeware's own scorer running our code. All five scored tasks are above ninety-nine point seven
> percent, and code quality is a hundred. And this is a rule, in plain Python.

## Scene 6 · 1:26–2:00 · Results, and new data

**Visual:** `02_score_climb.gif` (1:26–1:38), then `08_unseen_proof.png` (1:38–1:52), then a results card for the
last 8 seconds: "estimated 100% on every task (hand edits excluded) · code quality 100 · 286 of 286 unseen policies
end at 0".

**Narration (67 words):**
> Fifty-four rows are left. Thirty-eight are on Neuron's own list of hand edits, and sixteen more look just the same.
> Without hand edits, we estimate a hundred percent on every task. But does it work on new data? Two hundred
> eighty-six policies we had no answers for were cashed in. Our replay ends every one at exactly zero units. It works
> on data it has never seen.

## Production notes

- The total narration is 265 words. Read it aloud once with a timer before recording. If it runs long, cut the
  sentence about the decision tree in scene 3.
- Record the voice first, then cut the visuals to it. A GIF can loop if its scene runs longer than the animation.
- The demo must stay honest: show the real output, and label the sped-up part.
- Hold the final card still for 3 seconds after the last word.
- Upload the file to SwissTransfer and keep the link for the submission.
