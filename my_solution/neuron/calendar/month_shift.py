"""The calendar month `months` after the month of a date, as (year, month): month arithmetic in base 12, so January
2024 - 1 is December 2023 and November 2024 + 3 is February 2025."""


def month_shift(d, months):
    year, month = divmod(d.month - 1 + months, 12)
    return d.year + year, month + 1
