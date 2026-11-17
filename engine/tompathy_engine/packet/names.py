"""Stable reader identifiers. Display vocabulary is not a scientific mapping."""

NAMES = {
    "N1": "Knowledge", "N2": "Nest", "N3": "Belonging",
    "N4": "visibly respectable", "N5": "visibly compassionate", "N6": "the body",
    "C1": "SEEKING", "C2": "RAGE", "C3": "FEAR", "C4": "LUST", "C5": "CARE",
    "C6": "PANIC/GRIEF", "C7": "PLAY", "C8": "DISGUST", "C9": "SHAME",
    "S1": "Stress", "K1": "Capital",
}
NEEDS = tuple(key for key in NAMES if key.startswith("N"))
CHANNELS = tuple(key for key in NAMES if key.startswith("C"))
