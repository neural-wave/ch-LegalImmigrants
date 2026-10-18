"""The offer projection's growth of one month: a twelfth of the yearly illustration rate (NRILLU), linear, not
compounded within the year, rounded to the cent in the era of the application date."""
from neuron.contract import cents
from neuron.data import MONTHS


def grown(value, growth_rate, cobol):
    return cents(value * (1 + growth_rate / MONTHS), cobol)
