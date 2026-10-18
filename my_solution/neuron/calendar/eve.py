"""The day before a legacy date. A premium is converted into the fund currencies at the FX of the eve of its trade
date (seen in every PRM booking of t3), not at the FX of the trade date like the charges."""
import datetime as dt

from neuron.data import day
from neuron.legacy import legacy


def eve(legacy_date):
    return legacy(day(legacy_date) - dt.timedelta(days=1))
