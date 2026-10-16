"""Legacy dates: CYYMMDD decoding, month arithmetic, the COBOL/Java era split and Ticino business days.

All functions take and return `datetime.date`; the only state is the conversion date and the holiday list.
"""
import calendar
import datetime as dt
from decimal import ROUND_DOWN, ROUND_HALF_UP

# Neuron was converted from the COBOL system to the Java system on the weekend of 2007-08-11/12: the
# system conversion (event type 800) is dated 2007-08-11, so values up to 2007-08-10 follow the old arithmetic.
CONVERSION = dt.date(2007, 8, 11)
OPEN_END = dt.date(9999, 12, 31)
# Public holidays of canton Ticino from 2026-07-01 to 2027-06-30 (identical to `holidays.CH(subdiv="TI")`).
TICINO_HOLIDAYS = frozenset(dt.date.fromisoformat(d) for d in (
    "2026-08-01", "2026-08-15", "2026-11-01", "2026-12-08", "2026-12-25", "2026-12-26",
    "2027-01-01", "2027-01-06", "2027-03-19", "2027-03-29", "2027-05-01", "2027-05-06", "2027-05-17",
    "2027-05-27", "2027-06-29"))


def day(value):
    """CYYMMDD -> date, where C is 0 for 19xx and 1 for 20xx (`970630` = 1997-06-30).

    `0` means no date (None) and `9999999` open end (OPEN_END), see the conventions in SCHEMA.md.
    """
    n = int(value)
    if n == 0:
        return None
    if n == 9999999:
        return OPEN_END
    return dt.date(1900 + n // 10000, n // 100 % 100, n % 100)


def raw_day(value):
    """CYYMMDD -> (year, month, day) without validation.

    NRPERS holds impossible birth dates such as 1954-11-31 that Neuron still used for age calculations.
    """
    n = int(value)
    return 1900 + n // 10000, n // 100 % 100, n % 100


def add_months(date, months, anchor_day=None):
    """`months` after `date`, on `anchor_day` (default: the day of `date`).

    The day is clamped to the month length, so an anchor of 31 gives 30 April and 28/29 February.
    """
    years, month = divmod(date.month - 1 + months, 12)
    year, month = date.year + years, month + 1
    return dt.date(year, month, min(anchor_day or date.day, calendar.monthrange(year, month)[1]))


def is_legacy(date):
    """True for dates the COBOL system handled, i.e. before the conversion weekend.

    2007-08-10 (Friday) is the last COBOL day, 2007-08-13 (Monday) the first Java day.
    """
    return date < CONVERSION


def rounding(date):
    """Rounding mode of the system in charge on `date`.

    The COBOL era truncates to the cent (ROUND_DOWN), the Java system rounds half up.
    """
    return ROUND_DOWN if is_legacy(date) else ROUND_HALF_UP


def is_business_day(date):
    """Monday to Friday and not a Ticino public holiday.

    Neuron ran in Ticino, so direct debits follow the cantonal holiday calendar.
    """
    return date.weekday() < 5 and date not in TICINO_HOLIDAYS


def next_business_day(date):
    """`date` itself if it is a business day, else the first business day after it.

    Used for collection dates: a due date on a weekend or holiday is collected on the next working day.
    """
    while not is_business_day(date):
        date += dt.timedelta(days=1)
    return date
