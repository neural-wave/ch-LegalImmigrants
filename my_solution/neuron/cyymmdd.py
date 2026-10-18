"""Legacy dates are numbers CYYMMDD, C being the century after 1900: 1250131 is 2025-01-31 and 970630 is
1997-06-30. Kept as (year, month, day) numbers here, because a few birth dates are impossible (1954-11-31)."""


def parts(legacy_date):
    n = int(legacy_date)
    return 1900 + n // 10000, n // 100 % 100, n % 100
