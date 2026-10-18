"""A date back in the legacy CYYMMDD form, the inverse of data.day: 2026-06-30 is 1260630, the century after 1900
in front. Parameter tables and bookings are compared and looked up in this form."""


def legacy(d):
    return (d.year - 1900) * 10000 + d.month * 100 + d.day
