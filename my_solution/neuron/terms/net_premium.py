"""The invested part of a premium, premium x (1 - entry rate), before any rounding: the offer (t2) and the fund
accounting (t3, t4) both take it; the entry rate is an ENT agreement or the broker tier's rate (rates.py)."""


def net_premium(premium, entry_rate):
    return premium * (1 - entry_rate)
