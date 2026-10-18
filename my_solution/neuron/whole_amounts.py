"""Target minus our values, all whole amounts and one of them not zero: the trace of a manual correction
(hand_edits.py), which moves a value by whole euros, where a gap in a rule shows in cents."""


def moved_by_whole_amounts(target, ours):
    deltas = [t - o for t, o in zip(target, ours)]
    return any(deltas) and all(d == d.to_integral_value() for d in deltas)
