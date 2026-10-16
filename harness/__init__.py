"""Rule-finding harness of the Neuron migration challenge.

    from harness import evaluate, explain, search
    mm = evaluate("t2", predictions, targets_dir)   # exact scoring + policy features per row
    explain(mm)                                      # histogram, decision tree, change points, worst rows
    search("t2", build_fn, space)                    # greedy coordinate search over rule variants

Not part of the submission: it reads the target files, which submitted code must never do.
"""
from harness.evaluate import Mismatches, evaluate, read_predictions
from harness.explain import explain
from harness.search import search

__all__ = ["Mismatches", "evaluate", "explain", "read_predictions", "search"]
