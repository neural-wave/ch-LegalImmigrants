# Captions and interpretation

Detailed explanations live here so the figures can remain visually simple.
Use these as the starting point for LaTeX figure captions or video narration.

## 01 — A hidden system switch

**Suggested caption:** Exact-row mismatch rates for the offer maturity projection,
grouped by application quarter. The dashed line forces half-up rounding on every
offer; the solid line uses the historical rounding convention. All rates and age
conventions are unchanged. The conversion date, 11 August 2007, is derived from
event 800. The historical implementation matches 3,011 of 3,019 train targets;
uniform half-up matches 2,184. Remaining differences are retained in the plot.

The collector also ran uniform truncation (828 exact matches); those measurements
remain in the aggregate JSON but are omitted from the graphic to reduce clutter.
This is a training-data counterfactual, not a private-set accuracy measurement.

## 02 — From errors to rules

**Suggested caption:** The discovery workflow compares predictions with reference
outputs, explains error patterns, tests alternatives and verifies a candidate.
The resulting rules feed a shared execution engine operating on legacy records.
Targets support offline discovery and the permitted t5 analysis; they are not
inputs to ordinary submitted calculations. The diagram is conceptual.

The shared mechanisms include historical version selection, date rules, Decimal
arithmetic, fund replay and valuation. Several tasks reuse these mechanisms.

## 03 — Timing changes the tax

**Suggested caption:** Illustrative comparison of a historical-period calculation
with applying only the final rate. Invented gains of +80, −20 and +100 at rates
12.5%, 20% and 26% contribute +10, −4 and +26, totaling 32. Applying 26% to the
combined gain of 160 gives 41.60. This illustrates the implemented Italian SOS
calculation; it is not actual policy data or independent validation of that rule.

The three bars are gain amounts, not tax amounts. The two values on the right are
the resulting taxes under the two calculation choices.

## 04 — Released-sample fit

**Suggested caption:** Retrospective local re-scores of selected package-line
uploads on the same released sample files: 60 payout rows and 50 annual rows.
Upload #79 matches all rows. These samples were used during rule development;
the plot does not establish private-set accuracy. Uploads are equally spaced as
categories, not by elapsed time. Connected points do not isolate the causal effect
of any individual change.

Source: `DataAnalytics/analysis/local_rescore/sNN.json` on Git commit
`33a704650e1c6305159e91d2d307d02e9a0157d0`. This chart is not the live leaderboard.

## Design references

- [Datawrapper: text in data visualizations](https://www.datawrapper.de/blog/text-in-data-visualizations)
  — direct labeling, concise phrasing, restrained typography.
- [Nature: preparing figures](https://research-figure-guide.nature.com/figures/preparing-figures-our-specifications/)
  — readable labels, fewer text labels and avoiding overlap.
- [Nature Methods: Simplify to clarify](https://www.nature.com/articles/nmeth.1660)
  — remove redundant and decorative elements without removing necessary evidence.

## Journey expansion — 18 October

The reading order is in `journey.html`; `journey-preview.png` shows all ten scenes.
The first four masters remain available. Six new masters have matching light report
and dark 1920×1080 video versions. These are static assets, not a rendered video.

| Scene | Interpretation and source | Boundary |
|---|---|---|
| 05 Journey | Team says focus through #26 was original tasks; later tax work followed. PROJECT_STORY sections 3 and latest update. | Conceptual stages; widths do not encode duration. Parallel discoveries overlapped. |
| 06 Rounding counterfactual | Historical 3,011, half-up 2,184, truncation 828 exact rows out of 3,019. `data/rounding-evidence.json`. | Measured train fit at 8247f0f; only rounding helper changed. Eight residual mismatches remain. |
| 07 Hidden holdings | Held funds can affect allocation even when a zero-rounded charge has no export row. PROJECT_STORY 5.4 and its historical sources. | Schematic A/B/C funds; invented layout, not an individual policy or fresh allocation experiment. |
| 08 Exact-row masking | Correcting one of two wrong fields leaves the row score at zero. | Invented correctness pattern; six fields correspond to payout metric. Does not describe an observed hidden row. |
| 09 Calendar experiment | 150 dates changed, other payout columns and annual rows identical. `audit/upload49-results.json`. | Local on/off toggle on old #53 code, not current code or a live causal experiment. Does not prove the calendar is correct. |
| 10 Historical replay | Shared state plus explicit historical rules support value, tax and residual calculations. Current source and PROJECT_STORY 5/7. | Conceptual architecture, not complete function-call graph; not every task uses the same path. |

`report/images/` includes native single-column versions of 06 and 08 for readable
IEEE placement. The compact masking figure abbreviates country as Ctry and
surcharges as Extra and stamp duty as Duty. Rebuild with `python visualisation/src/build_journey.py`.

The new screenshot shows a third t7 evaluation set. Do not connect old live scores
as a same-test curve. Figure 04 is still a retrospective fixed-released-sample
comparison, not a live leaderboard progression. Latest screenshot transcription:
`data/latest-public-checkpoint.json`. No personal screenshot content is reproduced.
