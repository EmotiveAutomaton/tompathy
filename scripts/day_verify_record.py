"""Independent TP89 audit of the released record. No scoring or input corpora."""

import hashlib
import json
import re
from pathlib import Path


def main():
    root = Path("docs/exchange")
    entries = [
        json.loads(line)
        for line in Path("engine/validation/EVIDENCE_LEDGER.jsonl")
        .read_bytes()
        .splitlines()
    ]
    hashes = {}
    for number in range(61, 80):
        page = root / "r48" / f"TP{number}.md"
        body = page.read_text("utf8")
        if re.findall(r"(?m)^\*\*([1-7])\.", body) != list("1234567") or not re.search(
            r"(?m)^Limit: .+", body
        ):
            raise ValueError(f"Missing R48 field: {page}")
        for row in entries:
            if row["id"].startswith(f"E-TP{number}-") and (
                row["limit"] not in body or row["data"] not in body
            ):
                raise ValueError("Missing ledger limit or source table: " + row["id"])
        hashes[page.as_posix()] = hashlib.sha256(page.read_bytes()).hexdigest()
    family = (root / "result-sheets/TP78.md").read_text("utf8").splitlines()
    for key in ("TP64.1", "TP64.analyst", "TP65.1", "TP70.2", "TP70.analyst", "TP61.1"):
        [row] = [line for line in family if line.startswith(f"| {key} |")]
        if "| × " not in row:
            raise ValueError("Missing crossed prediction: " + key)
    src = json.loads(
        Path("engine/validation/readers-tp65-original-2026-11.json").read_bytes()
    )
    tab = src["sources"]["ed"]["B"]["contrasts"]["changeMinusNeither"]["outputs"]
    channel = {k: r for k, r in tab.items() if k != "worry"}
    lower = sorted(k for k, r in channel.items() if max(r["interval"]) < 0)
    higher = sorted(k for k, r in channel.items() if min(r["interval"]) > 0)
    assert lower == [
        "CARE",
        "DISGUST",
        "FEAR",
        "LUST",
        "PLAY",
        "SEEKING",
    ] and higher == ["RAGE"]
    page = (root / "result-sheets/TP65.md").read_text("utf8")
    for k, r in channel.items():
        [line] = [
            s
            for s in page.split("## Chat change sentences compared with neither")[
                1
            ].splitlines()
            if s.startswith("| " + k + " |")
        ]
        values = [float(x) for x in re.findall(r"-?\d+\.\d+", line)]
        if len(values) != 3 or any(
            abs(a - b) > 0.000006
            for a, b in zip(values, [r["value"], *r["interval"]], strict=True)
        ):
            raise ValueError("Reported channel estimate differs")
    print(
        json.dumps(
            {
                "reports": len(hashes),
                "chatChannels": len(channel),
                "belowZero": lower,
                "aboveZero": higher,
                "crossedRowsChecked": 6,
                "reportSha256": hashes,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
