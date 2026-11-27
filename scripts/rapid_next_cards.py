"""Advance prepared Round 37 CPU cards on the preceding dispatcher’s verified exit."""

import argparse
from pathlib import Path

from rapid_after_gpu import wait_predecessor
from rapid_cpu_dispatch import ROOT, check, confirmed, execute
from rapid_head_check import bound, pin, read
from word_table_lane import identity, lease, now, write

PREVIOUS = ROOT / "post-groups"
OUT = ROOT / "sentence-card-queue"
STAGES = {
    "TP65-inputs": ("rapid_sentence_data.py",),
    "TP65": ("rapid_sentence_contrasts.py", "rapid_agreement.py"),
    "TP77-original": ("rapid_agreement.py",),
    "Q31-inputs": (
        "rapid_blog_selection.py",
        "rapid_blog_gpu.py",
        "rapid_sentences.py",
    ),
}


def registration():
    previous = read(PREVIOUS / "armed.json")
    bound(PREVIOUS / "registration.json", previous["registration"])
    code = {
        n: pin(Path(__file__).with_name(n)) for files in STAGES.values() for n in files
    }
    return {
        "priorRegistration": previous["registration"],
        "priorOwner": previous["owner"],
        "stages": list(STAGES),
        "code": code,
    }


def run(h):
    plan = read(bound(OUT / "registration.json", h))
    if plan != registration():
        raise ValueError("The registered sentence and blog plans differ")
    with lease(OUT / "dispatch.lock"):
        owner = identity()
        done = {}
        try:
            write(
                OUT / "armed.json",
                {
                    "owner": owner,
                    "at": now(),
                    "registration": h,
                    "predecessor": plan["priorOwner"],
                },
            )
            if not (PREVIOUS / "complete.json").exists():
                wait_predecessor(plan["priorOwner"], check)
            prior = read(PREVIOUS / "complete.json")
            if (
                prior["owner"] != plan["priorOwner"]
                or set(prior["verified"]) != {"TP70-return", "TP64"}
                or any(
                    confirmed(ROOT / (k + "-a")) != v
                    for k, v in prior["verified"].items()
                )
            ):
                raise ValueError(
                    "Preceding research stages have not released and verified"
                )
            for card, files in STAGES.items():
                check()
                for n in files:
                    bound(Path(__file__).with_name(n), plan["code"][n])
                done[card] = execute(card)
                write(OUT / "progress.json", {"at": now(), "verified": done})
            write(
                OUT / "complete.json", {"at": now(), "owner": owner, "verified": done}
            )
        except Exception as exc:
            write(
                OUT / "stopped.json",
                {"at": now(), "owner": owner, "reason": str(exc), "verified": done},
            )
            raise


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--registration")
    args = p.parse_args()
    if args.registration:
        run(args.registration)
    else:
        from rapid_land import put

        f = OUT / "registration.json"
        put(f, registration())
        print(pin(f))
