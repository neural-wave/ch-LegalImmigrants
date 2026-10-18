"""Gregorian corrections of the lunar calendar for century C: C - C // 4 for the leap days the century years drop
(solar), (8C + 13) // 25 for the day the moon slips 8 times in 25 centuries (lunar)."""


def century_correction(century):
    return century - century // 4 - (8 * century + 13) // 25
