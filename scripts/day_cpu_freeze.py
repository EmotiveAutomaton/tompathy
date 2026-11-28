"""Make a source-only TP81 snapshot. Never copy a corpus or an existing run directory."""

import hashlib
import io
import json
import subprocess
import zipfile
from pathlib import Path


def main():
    day = Path(".local/day-20261128")
    dst = day / "TP81-plan.json"
    if dst.exists():
        raise FileExistsError("Preserve the registered plan")
    rev = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    root = day / "cpu-code" / rev
    data = subprocess.check_output(
        ["git", "archive", "--format=zip", rev, "scripts", "engine/tompathy_engine"]
    )
    pins = {}
    with zipfile.ZipFile(io.BytesIO(data)) as bundle:
        for item in bundle.infolist():
            name = Path(item.filename)
            if name.suffix != ".py" or name.is_absolute() or ".." in name.parts:
                continue
            file = root / name
            file.parent.mkdir(exist_ok=True, parents=True)
            raw = bundle.read(item)
            with file.open("xb") as f:
                f.write(raw)
            pins[name.as_posix()] = hashlib.sha256(raw).hexdigest()

    def pin(p):
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()

    cfg = {
        "commit": rev,
        "code": pins,
        "packetPin": pin("TOMPATHY_0.3_ENGINE_ONE_DAY_PACKET_2026-11-28.md"),
        "protocolPin": pin("docs/exchange/result-sheets/TP81.md"),
        "cutoffUnix": 1795968000,
    }
    dst.write_text(
        json.dumps(cfg, sort_keys=True) + "\n", encoding="utf8", newline="\n"
    )
    print(rev, pin(dst))


if __name__ == "__main__":
    main()
