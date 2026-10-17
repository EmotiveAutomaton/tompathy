"""Aggregate handoff snapshot, 2026-10-17; none of these admits a module."""
from copy import deepcopy

SL = "https://github.com/EmotiveAutomaton/sounding-line/blob/main/results/phase_2_4_stage_15/DRIVE/"
GHOST = "https://github.com/EmotiveAutomaton/ghost-scale-sim/blob/main/results/v23/packet-20261017/"
FINDINGS = [
    {"source": "Sounding Line V2", "claim": "A model that starts from everyone and adjusts a little for each writer forecast these writers better than population rates. Saved, exposed forecasts; 16,855 decisions from 61 writers. Writer-resampled 95% interval, conditional on saved fits; no new admission.", "number": .023962, "interval": [.017497, .030691], "unit": "half-Brier improvement", "evidenceStatus": "descriptive", "link": SL + "V2.md"},
    {"source": "Sounding Line V1", "claim": "In planted tests, these instruments found a writer's constant lean, not yet their taste or habits. Synthetic outcomes on fixed human-record covariates; this is not a limit on all possible readers.", "number": None, "interval": None, "unit": None, "evidenceStatus": "constructed-tested", "link": SL + "V1_PHASE0.md"},
    {"source": "Ghost R4", "claim": "In constructed worlds, the largest observed root-cue gain had no leaf evidence and planted cue reliability 0.99. Nominated setting, not confirmation or a real-page reliability estimate.", "number": .6431190348758995, "interval": [.6246675513184207, .6615705184333783], "unit": "nats", "evidenceStatus": "constructed-tested", "link": GHOST + "R4-MACHINE_CARD.json"},
    {"source": "Ghost N5", "claim": "In constructed worlds, correcting a reader's projection with population rates yielded this largest observed gain. Nominated setting; not a natural-data admission.", "number": .9492858677208594, "interval": [.9029064198370778, .9956653156046411], "unit": "nats", "evidenceStatus": "constructed-tested", "link": GHOST + "N5-MACHINE_CARD.json"},
    {"source": "Ghost N7", "claim": "In constructed worlds, a shared-shift correction to stated versus revealed preferences yielded this largest observed gain. Nominated setting; not confirmation or a personal-value measurement.", "number": .2501206917914891, "interval": [.2118192090342693, .2884221745487089], "unit": "nats", "evidenceStatus": "constructed-tested", "link": GHOST + "N7-MACHINE_CARD.json"},
]


def findings():
    return deepcopy(FINDINGS)
