"""How many days the Paschal full moon (`moon` days after 21 March) falls after a Sunday, 0 to 6: the Gregorian
weekday formula with the year's leap days and the century correction of the leap rule."""


def moon_weekday(year, moon):
    return (year + year // 4 + moon + 2 - year // 100 + year // 400) % 7
