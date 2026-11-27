"""Start the two registered card jobs after the blind grouping dispatcher releases."""

import argparse
from pathlib import Path

from rapid_after_gpu import wait_predecessor
from rapid_cpu_dispatch import ROOT, check, confirmed, execute
from rapid_head_check import bound, pin, read
from word_table_lane import identity, lease, now, write

PREVIOUS = ROOT / "TP70-queue"
STAGES = ("TP70-return", "TP64")
MODULES = (
    "rapid_group_return.py",
    "rapid_channel_words.py",
    "rapid_blind_groups.py",
    "rapid_nulls.py",
)


def register():
    from rapid_group_return import DESIGN

    if confirmed(ROOT / "TP70-design-a") != DESIGN:
        raise ValueError("Expected the verified grouping design")
    previous = read(PREVIOUS / "owner.json")
    code = {name: pin(Path(__file__).with_name(name)) for name in MODULES}
    if any(previous["code"][name] != code[name] for name in previous["code"]):
        raise ValueError("Active grouping source changed")
    return {
        "stages": list(STAGES),
        "predecessor": previous["owner"],
        "design": DESIGN,
        "code": code,
        "packetPin": pin(Path("TOMPATHY_0.3_ENGINE_TWO_DAY_PACKET_2026-11-27.md")),
    }


def run(regpin):
    control = ROOT / "post-groups"
    control.mkdir(exist_ok=True)
    reg = read(bound(control / "registration.json", regpin))
    if reg != register():
        raise ValueError("Current jobs differ from the registered handoff")
    with lease(control / "dispatch.lock"):
        me = identity()
        done = {}
        try:
            write(
                control / "armed.json",
                {
                    "at": now(),
                    "owner": me,
                    "registration": regpin,
                    "predecessor": reg["predecessor"],
                },
            )
            if not (PREVIOUS / "complete.json").is_file():
                wait_predecessor(reg["predecessor"], check)
            previous = read(PREVIOUS / "complete.json")
            if (
                previous["owner"] != reg["predecessor"]
                or len(previous["verified"]) != 41
            ):
                raise ValueError(
                    "All forty grouping blocks must complete under the registered dispatcher"
                )
            for name in STAGES:
                check()
                for filename, h in reg["code"].items():
                    bound(Path(__file__).with_name(filename), h)
                done[name] = execute(name)
                write(control / "progress.json", {"at": now(), "verified": done})
            write(
                control / "complete.json", {"at": now(), "owner": me, "verified": done}
            )
        except Exception as exc:
            write(
                control / "stopped.json",
                {"at": now(), "owner": me, "verified": done, "reason": str(exc)},
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

        f = ROOT / "post-groups/registration.json"
        put(f, register())
        print(pin(f))
