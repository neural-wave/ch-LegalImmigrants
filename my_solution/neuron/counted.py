"""The bookings that count in the fund accounting: those whose event was not skipped, i.e. not reversed, not a
reversal and not a technical correction (reversals.py)."""


def counted(bookings, skipped):
    return [b for b in bookings if b.event not in skipped]
