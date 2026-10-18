"""The units a pot holds after a booking: what it held plus the booking's units (negative for charges and sales).
`units` is the running {(fund, pot): units} of the replay; the new position is returned."""


def booked(units, row):
    key = row.key
    units[key] += row.units
    return units[key]
