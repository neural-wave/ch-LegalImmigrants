"""COBOL Neuron calculated every date before the conversion to Java (event 800, contract.py); Java Neuron (Neuron
NG) calculated the conversion day and everything after it."""


def is_cobol(legacy_date, conversion):
    return int(legacy_date) < conversion
