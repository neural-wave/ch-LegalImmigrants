"""t1 next due dates: premium due dates after the extract date, with their collection dates.

Policies in force and paying regular premiums on the extract date (neuron/regular_premiums.py), due dates up to one
year later (neuron/calendar/due_window.py), collected by direct debit or bank transfer (neuron/calendar/collection.py).
"""
import datetime as dt
import itertools

from neuron.calendar.collection import collection_date
from neuron.calendar.due_dates import due_dates
from neuron.calendar.due_window import upcoming
from neuron.contract import conversion_date
from neuron.data import FREQ_MONTHS, as_of, day, grouped, guarded
from neuron.legacy import legacy
from neuron.terms.regular_premiums import pays_regularly


def next_due_dates(policy_id, versions, extract_date, conversion):
    """[((policy_id, n), (due_date, collection_date))] of one policy, n = 1, 2, ...; [] unless it pays regularly."""
    policy = as_of(versions, "PH", legacy(extract_date))
    if pays_regularly(policy):
        start, end = day(policy["PH_BEGDT"]), day(policy["PH_ENDDT"])
        dues = upcoming(due_dates(start, FREQ_MONTHS[policy["PH_FREQ"]], conversion, end), extract_date)
        return [((policy_id, n), (due, collection_date(due, policy["PH_PAYMT"]))) for n, due in enumerate(dues, 1)]
    return []


def t1_next_due_dates(legacy_dir, extract_date: dt.date) -> dict[tuple[str, int], tuple[dt.date, dt.date]]:
    """{(policy_id, n): (due_date, collection_date)} for the due dates after `extract_date`, n = 1, 2, ...

    Policies with incomplete data are left out.
    """
    conversion = day(conversion_date(legacy_dir))
    policies = grouped(legacy_dir, "NRPOLH", "PH_POLNR").items()
    rows = (guarded(next_due_dates, policy_id, versions, extract_date, conversion) for policy_id, versions in policies)
    return dict(itertools.chain.from_iterable(filter(None, rows)))
