"""Age of the insured person for the risk charge, shared by the offer projection (t2) and the charge run (t3/t4).

Rules found:
- the era is keyed by the APPLICATION date of the policy and sticks for its whole life;
- COBOL offers: age at entry = nearest birthday from the calendar days between birth and start / 365
  (impossible birth days clipped to the month end), then + 1 per completed policy year, never recomputed;
- Java offers: nearest birthday in whole months at the policy anniversary.
"""
import calendar
import datetime as dt

from dates import is_legacy


def entry_age(begin, birth):
    """COBOL age at entry: nearest birthday from the calendar days between birth and start, divided by 365.

    `birth` is the raw (year, month, day); an impossible day (1954-11-31) is clipped to the month end.
    floor(days / 365 + 0.5): the leap days since birth push older lives up by a year now and then.
    """
    year, month, day_ = birth
    # NRPERS holds impossible days (31 November): COBOL clipped them to the last day of the month
    born = dt.date(year, month, min(day_, calendar.monthrange(year, month)[1]))
    # integer form of floor(days / 365 + 0.5)
    return ((begin - born).days * 2 + 365) // 730


def risk_age(applied, begin, birth, policy_year):
    """Age the risk charge uses in policy year `policy_year` (0 = the first year), `birth` = raw (y, m, d).

    Policies applied for in the COBOL era keep its rule for their whole life: the entry age plus the completed
    policy years. Java offers take the nearest birthday in whole months at the anniversary: a started month
    counts only once the birthday day is reached.
    """
    if is_legacy(applied):
        # COBOL: the age is incremented per policy year, never recomputed from the calendar
        return entry_age(begin, birth) + policy_year
    # Java: whole months of age at the anniversary, rounded to the nearest birthday
    months = (begin.year + policy_year - birth[0]) * 12 + begin.month - birth[1] - (begin.day < birth[2])
    return (months + 6) // 12
