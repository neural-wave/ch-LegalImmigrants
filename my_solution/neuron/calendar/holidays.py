"""The public holidays of canton Ticino (Switzerland), where NeuralWave Life collects its direct debits, for
every currency: no Good Friday, but St Joseph (19 Mar), Corpus Christi, Sts Peter and Paul (29 Jun) and the
Immaculate Conception (8 Dec). Fixed (month, day) dates, plus days counted from Easter Sunday."""
import datetime as dt

from neuron.calendar.easter import easter

FIXED_HOLIDAYS = ((1, 1), (1, 6), (3, 19), (5, 1), (6, 29), (8, 1), (8, 15), (11, 1), (12, 8), (12, 25), (12, 26))
EASTER_HOLIDAYS = (1, 39, 50, 60)  # Easter Monday, Ascension, Whit Monday, Corpus Christi


def holidays(year):
    moving = (easter(year) + dt.timedelta(days=n) for n in EASTER_HOLIDAYS)
    return {*(dt.date(year, m, d) for m, d in FIXED_HOLIDAYS), *moving}
