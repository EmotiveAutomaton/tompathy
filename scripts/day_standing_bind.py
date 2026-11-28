"""Create a new chat handoff from the existing Q27 return and the exact G12 floor stop."""

from pathlib import Path

from rapid_standing_return import REG, ROOT, windows
from word_table_lane import pin, read, write


def bind():
    original = ROOT / "standing-return"
    path = original / "registration.json"
    if pin(path) != read(original / "armed.json")["registrationPin"]:
        raise ValueError("Original standing watcher registration differs")
    plan = read(path)
    w = windows(plan)
    b = read(ROOT / "Q27-transfer.json")
    folder = Path(b["mirror"])
    if (
        b["owner"]["registration"] != REG
        or b["owner"]["job"] != "Q27"
        or any(b["owner"][k] != v for k, v in plan["B"].items())
        or not b["nativeExited"]
        or not b["ownedFlockReleased"]
        or b["release"]["exitCode"]
        or b["release"]["owner"] != b["owner"]
        or pin(folder / "receipt.json") != b["sourceReceiptPin"]
        or read(folder / "complete.json") != {"sourceReceiptPin": b["sourceReceiptPin"]}
        or w["status"] != "memory-prefix"
        or w["sources"]["ed"]["rows"] != 24850
    ):
        raise ValueError("The frozen Q27 return or chat prefix proof differs")
    dst = ROOT.parent / "day-20261128/standing-chat-handoff.json"
    receipt = {
        "B": b,
        "W": w,
        "source": "ed",
        "registration": REG,
        "sourceReceiptTypeW": "verified prefix manifest",
    }
    if dst.exists():
        if read(dst) != receipt:
            raise ValueError("Preserve earlier prefix handoff")
    else:
        write(dst, receipt)
    print(pin(dst), w["sources"]["ed"])


if __name__ == "__main__":
    bind()
