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


BLEND_FILES = ("rapid_blend.py", "rapid_content.py")
OUTSIDE_STAGES = {
    "TP63-original": ("rapid_outside.py", "rapid_nulls.py"),
    "TP68-design": BLEND_FILES,
    **{f"TP68-fold-{i}": BLEND_FILES for i in range(5)},
    "TP68-return": BLEND_FILES,
}


def configuration(queue):
    if queue == "sentence":
        return PREVIOUS, OUT, {"TP70-return", "TP64"}, STAGES
    if queue == "outside":
        return OUT, ROOT / "outside-card-queue", set(STAGES), OUTSIDE_STAGES
    raise ValueError("Unknown packet queue")


def registration(queue="sentence"):
    earlier, _, _, stages = configuration(queue)
    previous = read(earlier / "armed.json")
    bound(earlier / "registration.json", previous["registration"])
    code = {
        n: pin(Path(__file__).with_name(n)) for files in stages.values() for n in files
    }
    result = {
        "priorRegistration": previous["registration"],
        "priorOwner": previous["owner"],
        "stages": list(stages),
        "code": code,
    }
    if queue == "outside":
        result["protocols"] = {
            k: pin(Path(f"docs/exchange/result-sheets/{k}.md"))
            for k in ("TP63", "TP68")
        }
    return result


def run(h, queue="sentence"):
    earlier, out, required, stages = configuration(queue)
    plan = read(bound(out / "registration.json", h))
    if plan != registration(queue):
        raise ValueError("The registered study plans differ")
    with lease(out / "dispatch.lock"):
        owner = identity()
        done = {}
        try:
            write(
                out / "armed.json",
                {
                    "owner": owner,
                    "at": now(),
                    "registration": h,
                    "predecessor": plan["priorOwner"],
                },
            )
            if not (earlier / "complete.json").exists():
                wait_predecessor(plan["priorOwner"], check)
            prior = read(earlier / "complete.json")
            if (
                prior["owner"] != plan["priorOwner"]
                or set(prior["verified"]) != required
                or any(
                    confirmed(ROOT / (k + "-a")) != v
                    for k, v in prior["verified"].items()
                )
            ):
                raise ValueError(
                    "Preceding research stages have not released and verified"
                )
            for card, files in stages.items():
                check()
                if card in ("TP63-original", "TP68-design"):
                    key = card.split("-")[0]
                    bound(
                        Path(f"docs/exchange/result-sheets/{key}.md"),
                        plan["protocols"][key],
                    )
                for n in files:
                    bound(Path(__file__).with_name(n), plan["code"][n])
                done[card] = execute(card)
                write(out / "progress.json", {"at": now(), "verified": done})
            write(
                out / "complete.json", {"at": now(), "owner": owner, "verified": done}
            )
        except Exception as exc:
            write(
                out / "stopped.json",
                {"at": now(), "owner": owner, "reason": str(exc), "verified": done},
            )
            raise


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--registration")
    p.add_argument("--queue", choices=("sentence", "outside"), default="sentence")
    args = p.parse_args()
    if args.registration:
        run(args.registration, args.queue)
    else:
        from rapid_land import put

        f = configuration(args.queue)[1] / "registration.json"
        put(f, registration(args.queue))
        print(pin(f))
