# Neuron, revealed

Four visual stories about reconstructing an undocumented insurance engine.
Start with [`index.html`](index.html), or the four-up [`preview.png`](preview.png).
The graphics use short titles and direct labels. Detailed interpretation is in
[`CAPTIONS.md`](CAPTIONS.md), ready to adapt for LaTeX or narration.

## Choose a visual

| Figure | The point | Evidence | Suggested use |
|---|---|---|---|
| `01-rounding-discovery` | One hidden historical boundary explains a strong error pattern | Fresh t2 counterfactual run on 3,019 train targets | Main discovery figure; animated reveal in video |
| `02-shared-engine` | The discovery method produces reusable rules; several tasks share the financial engine | Architecture schematic based on current source | Method/architecture section |
| `03-historical-tax-periods` | One final tax rate differs from the implemented historical-period calculation | Explicitly invented arithmetic illustrating `Ledger.gain_tax` | Technical explanation; reveal one period at a time |
| `04-sample-evidence` | Later rules explain all released sample rows, with an important evaluation limit | Recorded local re-scores of uploads #53, #57, #64, #75, #79 | Results and limitations, not private-set performance |

## Two visual treatments

- **`report/`**: light background, 7.16-inch double-column figure masters, PDF + SVG + 300 dpi PNG.
- **`video/`**: dark background, 1920×1080 PNG + SVG. Static scene assets ready for later animation.
- **`data/`**: aggregate evidence and provenance; no policy IDs or individual tax amounts.
- **`src/`**: reproducible collection and rendering scripts. Submission code stays untouched.

Use PDF files with LaTeX. The complex figures are designed for two columns; do not shrink
them to one column without simplifying them. Example:

```latex
\begin{figure*}[t]
  \centering
  \includegraphics[width=\textwidth]{visualisation/report/01-rounding-discovery.pdf}
  \caption{Holding rates and age conventions fixed, replacing historical rounding
  with either uniform rounding convention produces an error pattern around the
  conversion date. The historical rule matches 3,011 of 3,019 training targets.}
  \label{fig:rounding-discovery}
\end{figure*}
```

## Evidence boundaries

1. Figure 01 re-runs the current working tree at commit
   `8247f0f43fd91c5fbdadbfd9ce64fb0cb9747798`. The conversion date comes from event 800.
   Only `neuron.contract.rounding` is replaced temporarily, in-process. Rates and
   risk-age conventions stay fixed. Results: historical 3,011/3,019; uniform half-up
   2,184/3,019; uniform truncation 828/3,019. The figure displays the historical and
   uniform half-up scenarios only; truncation is retained in the data. Quarter bins include altered targets.
   The plot is not a claim of zero remaining error or private-set validation.
2. Figure 02 is a conceptual architecture diagram, not a measured call graph.
3. Figure 03 uses invented gain units (+80, −20, +100). It contains no policy data.
   The rates and calculation structure reflect the implementation. This is an
   explanation of the rule, not independent evidence that Neuron used it.
4. Figure 04 reads `DataAnalytics/analysis/local_rescore/sNN.json` from branch commit
   `33a704650e1c6305159e91d2d307d02e9a0157d0`. It combines sample 1 and sample 2:
   60 payout and 50 annual rows. These samples were used during rule development.
   The figure does not report leaderboard scores, changes caused by isolated
   experiments, elapsed time, or accuracy of the current commit on unseen data.
   Snapshot spacing is categorical. Do not relabel this as a generalization curve.

## Rebuild

From the repository root, Python 3.10+:

```bash
python3 -m venv visualisation/.venv
visualisation/.venv/bin/pip install -r visualisation/requirements.txt
visualisation/.venv/bin/python visualisation/src/collect_evidence.py
visualisation/.venv/bin/python visualisation/src/build_figures.py
```

Collection expects the local legacy/target export under `LifewareChallenge/participants/`.
Use `--legacy` and `--targets` for other locations. The `DataAnalytics` branch must
be available locally for the recorded re-scores. Rendering alone needs only the
included aggregate JSON files. The temporary environment used for the first build
was `/private/tmp/neuron-viz-env`; it is not part of this folder.

## Editorial guidance

For a short IEEE-style paper, prioritize 01 and 02, add 03 if space permits,
and put full results in a table. Figure 04 is useful for discussing evidence limits.
For video, reveal the counterfactuals in 01 one at a time, then the shared engine,
then the rate periods in 03. Keep the evidence labels visible.

These are static scene assets, not a rendered video. The HTML gallery only browses
local files and does not publish anything. No submission source files were changed.

## Chronological journey expansion

Start with **[journey.html](journey.html)** or **[journey-preview.png](journey-preview.png)**
for the expanded ten-scene story. Six new masters cover investigation stages,
rounding alternatives, hidden holdings, masked exact-row improvements, the
controlled calendar toggle and the resulting historical replay. Their evidence
and captions are in CAPTIONS.md. Rebuild the expansion with:

```bash
python visualisation/src/build_journey.py
```

The report draft is in `../report/main.tex`. Its latest public checkpoint is
provisional; an additional run is planned. Old scores spanning different t7 target
sets are deliberately not joined into a live learning curve.
