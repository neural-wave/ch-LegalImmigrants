"""What each pot has left after the admin fee and the management charge of a run: the risk charge is taken on it
and shared by it (`risk_charge`, `split`, replay.py)."""


def left_after(values, admin, management):
    return {k: v - admin[k] - management[k] for k, v in values.items()}
