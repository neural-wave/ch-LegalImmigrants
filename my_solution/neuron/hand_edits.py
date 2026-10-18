"""A manual correction (t5) moves a value by a whole, non-zero amount: t0 by +9 to +77, t3 and t4 by +7 to +499,
t2 by thousands (whole_amounts.py). Without a value of ours (None: incomplete data) nothing can be judged."""
from neuron.whole_amounts import moved_by_whole_amounts


def hand_edited(target, ours):
    return ours is not None and None not in ours and moved_by_whole_amounts(target, ours)
