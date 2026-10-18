"""Events whose bookings don't count (NRCODE EVTTP): an event reversed by a 900, whose EV_REVNR names it, the
reversal itself and technical corrections (990); counted.py and the t5 check (charge_runs.py) leave them out."""
REVERSAL_EVENT, CORRECTION_EVENT = "900", "990"


def skipped_events(events):
    cancelled = {int(e["EV_REVNR"]) for e in events.values() if e["EV_EVTTP"] == REVERSAL_EVENT}
    return cancelled | {n for n, e in events.items() if e["EV_EVTTP"] in (REVERSAL_EVENT, CORRECTION_EVENT)}
