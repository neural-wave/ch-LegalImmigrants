"""Easter Sunday in the Gregorian calendar: the Sunday after the Paschal full moon (paschal_moon.py). Backing up from
the full moon to the Sunday on or before it (moon_weekday.py) and adding a week gives 28 March plus those days.
Four Ticino holidays move with it (holidays.py)."""
import datetime as dt

from neuron.calendar.moon_weekday import moon_weekday
from neuron.calendar.paschal_moon import paschal_moon


def easter(year):
    moon = paschal_moon(year)
    return dt.date(year, 3, 28) + dt.timedelta(days=moon - moon_weekday(year, moon))
