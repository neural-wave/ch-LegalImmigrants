"""The two exceptions of the Gregorian computus that keep Easter on or before 25 April: a Paschal full moon 29 days
after 21 March moves to day 28, and one on day 28 moves to 27 when the golden number is above 10."""


def corrected(moon, golden):
    return moon - (moon // 28) * (1 - (29 // (moon + 1)) * ((21 - golden) // 11))
