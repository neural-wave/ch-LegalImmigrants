"""The offer projection's premium month: the premium net of the entry charge comes in on month 0 and then every
`step` months (the premium frequency); a single premium steps over the whole projection, so it comes in once."""


def with_premium(value, premium, month, step):
    return value + premium * (month % step == 0)
