"""Calendar years with an annual statement (t4): from the start year to the year the policy ended by surrender or
death (ended.py, the year its version in that state became valid), at the latest the last full calendar year before
the extract date 2026-06-30."""
from neuron.cyymmdd import parts
from neuron.ended import has_ended

LAST_YEAR = 2025


def statement_years(policy):
    ended = [parts(v["PH_VLDFR"])[0] for v in policy.versions if has_ended(v)]
    return range(policy.start.year, min([*ended, LAST_YEAR]) + 1)
