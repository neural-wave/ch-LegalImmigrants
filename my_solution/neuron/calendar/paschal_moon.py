"""Days from 21 March to the Paschal full moon of a year (Oudin's algorithm, as in Tøndering's calendar FAQ): the
golden number places the year in the 19-year lunar cycle (lunar_cycle.py), then the two exceptions apply
(moon_exceptions.py)."""
from neuron.calendar.lunar_cycle import uncorrected_moon
from neuron.calendar.moon_exceptions import corrected


def paschal_moon(year):
    golden = year % 19
    return corrected(uncorrected_moon(golden, year // 100), golden)
