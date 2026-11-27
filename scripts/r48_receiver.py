"""Import the registered receiver's released TMP2 status and empty table at the reviewed commit."""

import argparse
import csv
import hashlib
import io
import json
import subprocess
from pathlib import Path

REV = "18708a8f11e17e33bcd8717a21e330a8257bb2cd"
TABLE = "docs/exchange/r48/TMP2-source.csv"
RECEIPT = "results/phase_2_4_stage_15/WEEK8/TMP2_DJ_SOURCE_AND_FALLBACK_REHEARSAL.json"
COLUMNS = "quantity,estimate,lower,upper,size,unit,observations,reading"


def project(repo):
    def blob(name):
        return subprocess.check_output(
            ["git", "-C", str(repo), "show", f"{REV}:{name}"]
        )

    table, receipt = blob(TABLE), blob(RECEIPT)
    if list(csv.reader(io.StringIO(table.decode("utf8")))) != [COLUMNS.split(",")]:
        raise ValueError(
            "This registration accepts only the reviewed header-only release"
        )
    status = json.loads(receipt)
    if (
        status["card"],
        status["native_exit"],
        status["launcher_exit"],
        status["gate"],
    ) != ("TMP2", 22, 4, "skipped"):
        raise ValueError("Receiver source status differs")
    return {
        "revision": REV,
        "table": TABLE,
        "receipt": RECEIPT,
        "tableSha256": hashlib.sha256(table).hexdigest(),
        "receiptSha256": hashlib.sha256(receipt).hexdigest(),
        "nativeExit": status["native_exit"],
        "launcherExit": status["launcher_exit"],
        "gate": status["gate"],
        "rows": [],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receiver", type=Path)
    args = parser.parse_args()
    path = Path("engine/validation/r48-tmp2-source-2026-11.json")
    path.write_text(
        json.dumps(project(args.receiver), indent=2) + "\n",
        encoding="utf8",
        newline="\n",
    )
