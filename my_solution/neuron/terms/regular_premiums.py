"""Which policies have upcoming due dates (t1): a version valid on the extract date, in force and paying regular
premiums (NRCODE STATE 10), monthly to yearly (PH_FREQ M, Q, H or J); single premiums (E) have none."""
from neuron.data import FREQ_MONTHS

PAYING = "10"


def pays_regularly(version):
    return bool(version) and version["PH_STATE"] == PAYING and version["PH_FREQ"] in FREQ_MONTHS
