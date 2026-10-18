"""A policy ended by surrender (state 60) or by a death claim (state 70) has paid out: from the version in that
state on it is worth nothing (t3) and gets no more annual statements (t4)."""
ENDED = ("60", "70")  # NRCODE STATE


def has_ended(version):
    return version["PH_STATE"] in ENDED
