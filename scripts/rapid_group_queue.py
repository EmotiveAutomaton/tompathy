"""Advance TP70 at verified workstation block boundaries."""

from pathlib import Path

from rapid_cpu_dispatch import ROOT, check, confirmed, execute
from word_table_lane import identity, lease, now, pin, write


def run():
    scripts = Path(__file__).resolve().parent
    ctl = ROOT / "TP70-queue"
    ctl.mkdir(exist_ok=True)
    with lease(ctl / "dispatch.lock"):
        code = {
            k: pin(scripts / k) for k in ("rapid_blind_groups.py", "rapid_nulls.py")
        }
        owner = identity()
        done = {}
        write(ctl / "owner.json", {"owner": owner, "at": now(), "code": code})
        try:
            confirmed(ROOT / "TP61-words-a")
            confirmed(ROOT / "TP62-block-09-a")
            for card in ["TP70-design", *(f"TP70-block-{i:02d}" for i in range(40))]:
                check()
                if any(pin(scripts / k) != h for k, h in code.items()):
                    raise ValueError("Registered grouping implementation differs")
                done[card] = execute(card)
                write(ctl / "progress.json", {"at": now(), "verified": done})
            write(
                ctl / "complete.json", {"at": now(), "owner": owner, "verified": done}
            )
        except Exception as error:
            write(
                ctl / "stopped.json",
                {"at": now(), "reason": str(error), "verified": done},
            )
            raise


if __name__ == "__main__":
    run()
