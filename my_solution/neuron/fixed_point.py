"""Fixed-point legacy numbers N(s) are integers with s implied decimals: num('31500', 2) = 315.00 and rates
N(6) num('30000', 6) = 0.03. A blank field is 0."""
from decimal import Decimal


def num(value, scale):
    return Decimal(int(value or 0)).scaleb(-scale)
