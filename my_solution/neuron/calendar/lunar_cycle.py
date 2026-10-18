"""Days from 21 March to the Paschal full moon before the two exceptions: 19 days later per year of the 19-year lunar
cycle (the golden number), shifted by the century corrections (century_correction.py), modulo a lunar month of 30."""
from neuron.calendar.century_correction import century_correction


def uncorrected_moon(golden, century):
    return (century_correction(century) + 19 * golden + 15) % 30
