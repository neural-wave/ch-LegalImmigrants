"""The monthly charge runs of a policy that count: its events of type 300 (NRCODE EVTTP) that were not reversed
by a 900 (contract.skipped). Each took the admin fee, management and risk charges of its month."""
CHARGE_RUN = "300"


def charge_runs(policy):
    return [e for n, e in policy.events.items() if e["EV_EVTTP"] == CHARGE_RUN and n not in policy.skipped]
