"""Transcribe Round 38 registered directions into TP78 without inspecting new outcomes."""

from pathlib import Path

PACKET = Path("TOMPATHY_0.3_ENGINE_ONE_DAY_PACKET_2026-11-28.md")
# Each entry is one claimant's registered conjunction. Descriptions receive no family test.
CLAIMS = {
    "TP80.thread": (
        "results thread",
        "With topic held, the trained tags' median repeat falls inside the rotated band.",
    ),
    "TP81.thread": (
        "results thread",
        "At least 73 of 145 item-agreement ceilings are under 0.2.",
    ),
    "TP82.seeking": ("curator", "Competence has the highest keyed SEEKING cell."),
    "TP82.pride": (
        "curator versus thread",
        "PRIDE Competence minus Respect is positive for the curator and negative for the thread.",
    ),
    "TP82.sadness": (
        "thread versus curator",
        "For loss texts, SADNESS Belonging minus the other needs is positive for the thread. A zero contrast has no equivalence margin.",
    ),
    "TP82.body": (
        "thread",
        "Body has the highest keyed FEAR, DISGUST and SHAME cells.",
    ),
    "TP82.savings": (
        "curator",
        "Savings accompanies Respect more than order and serenity. Descriptive tag comparison.",
    ),
    "TP82.rage": (
        "thread",
        "Power and order accompany RAGE. Descriptive tag comparison.",
    ),
    "TP82.lust": (
        "curator",
        "LUST cares about status. The available output measures wanting.",
    ),
    "TP83.curator": ("curator", "Own doing raises PRIDE. Standing alone does not."),
    "TP83.thread": ("results thread", "Standing raises PRIDE. Own doing adds nothing."),
    "TP83.print": ("print", "Both standing and own doing raise PRIDE."),
    "TP84.curator": ("curator", "No difference between need groups."),
    "TP84.thread": ("results thread", "SADNESS is highest where Belonging leads."),
    "TP85.curator": (
        "curator, from Klinger",
        "SEEKING before RAGE, and RAGE before SADNESS.",
    ),
    "TP85.theory": ("theory and research thread", "RAGE before SADNESS."),
    "TP85.results": ("results thread", "FEAR and RAGE before SADNESS."),
    "TP86.thread": (
        "results thread",
        "Suddenness alone distinguishes surprised better than the ten outputs and SEEKING comes late.",
    ),
    "TP86.print": ("print", "SEEKING is raised in surprised texts."),
}
OUTSIDE = {"TP88.analyst", "TP90.analyst", "TP82.savings", "TP82.rage", "TP82.lust"}
MISSED = {
    "TP64.1": "LUST distinguished desire from excitement above the registered 0.70 ceiling.",
    "TP64.analyst": "The LUST contrast with excitement exceeded 0.70.",
    "TP65.1": "Six chat outputs fell on change versus neither.",
    "TP70.2": "The thread's excess was lower than the map's in both sources.",
    "TP70.analyst": "The blog floor was three and the map had greater excess.",
}


def rows():
    result = dict(CLAIMS)
    for line in PACKET.read_text("utf8").split("## 7.")[1].splitlines():
        if line.startswith("| TP"):
            card, guess, rival = (s.strip() for s in line.strip("|").split("|"))
            result[card + ".analyst"] = ("analyst", guess + " Rival: " + rival)
    return result
