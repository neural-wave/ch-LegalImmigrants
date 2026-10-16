"""t1: due dates after the extract date and their collection dates (100 % on the train targets).

Rules found:
- only policies whose version valid on the extract date is in state 10 with a regular frequency (M/Q/H/J);
- due dates are start date + k x frequency months, the day of month clamped to the month length;
- COBOL era: the day of month is anchored on the last due date before the conversion (a clamped day stays
  clamped, e.g. 30 after a February), Java era: on the day of the start date;
- due dates run up to one year after the extract date and stop before the maturity date;
- direct debit (LS) collects on the next Ticino business day, other payment methods on the due date.
"""
from dates import CONVERSION, OPEN_END, add_months, day, next_business_day
from loader import grouped
from params import policy_version

FREQUENCY_MONTHS = {"M": 1, "Q": 3, "H": 6, "J": 12}


def anchor_day(version, past_dues):
    """Day of month of the instalment schedule.

    Java era: the day of the start date. COBOL era: the day of the last due date before the conversion,
    because the old system carried a clamped day (e.g. 28 after February) forward instead of the start day.
    """
    begin = day(version["PH_BEGDT"])
    before = [d for d in past_dues if d < CONVERSION]
    return before[-1].day if begin < CONVERSION and before else begin.day


def due_dates(version, anchor, extract_date):
    """Due dates in (extract_date, extract_date + 12 months] that lie before the maturity date.

    The loop starts a few instalments before the extract date instead of at the policy start (speed only).
    """
    begin, step = day(version["PH_BEGDT"]), FREQUENCY_MONTHS[version["PH_FREQ"]]
    end, horizon = day(version["PH_ENDDT"]) or OPEN_END, add_months(extract_date, 12)
    k = max(0, ((extract_date.year - begin.year) * 12 + extract_date.month - begin.month - 1) // step)
    dues = []
    while (due := add_months(begin, k * step, anchor)) <= horizon and due < end:
        if due > extract_date:
            dues.append(due)
        k += 1
    return dues


def collection_date(due, payment_method):
    """Day the premium is collected.

    LS (direct debit) is collected on the next business day, every other payment method on the due date.
    """
    return next_business_day(due) if payment_method == "LS" else due


def solve(legacy_dir, extract_date):
    """{(policy_id, n): (due_date, collection_date)}

    Policies without a version valid on the extract date, not in state 10 or with a single premium are skipped.
    """
    items = grouped(legacy_dir, "NRPREM", "PR_POLNR")
    out = {}
    for policy in grouped(legacy_dir, "NRPOLH", "PH_POLNR"):
        version = policy_version(legacy_dir, policy, extract_date)
        if version is None or version["PH_STATE"] != "10" or version["PH_FREQ"] not in FREQUENCY_MONTHS:
            continue
        past = sorted(day(i["PR_DUEDT"]) for i in items.get(policy, []))
        for n, due in enumerate(due_dates(version, anchor_day(version, past), extract_date), 1):
            out[(policy, n)] = (due, collection_date(due, version["PH_PAYMT"]))
    return out
