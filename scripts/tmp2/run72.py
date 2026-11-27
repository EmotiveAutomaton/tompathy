"""Offline entry points. Paths are receiver scratch within the sealed job."""

import argparse
import json
import sys
from pathlib import Path
from types import SimpleNamespace


def offline(event, unused):
    if event.startswith("socket."):
        raise RuntimeError("Network use refused")


def main():
    sys.addaudithook(offline)
    from panels import Frozen

    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("history", "conversation"))
    parser.add_argument(
        "projection",
        type=Path,
        help="History directory or projected speaker JSONL, or - for stdin",
    )
    parser.add_argument("scratch", type=Path)
    args = parser.parse_args()
    if args.scratch.exists():
        raise FileExistsError("Require fresh private scratch")
    frozen = Frozen()
    if args.mode == "history":
        from history import history

        history(args.projection, args.scratch, frozen)
    else:
        from contextlib import nullcontext

        from conversation import conversation

        source = (
            nullcontext(sys.stdin)
            if args.projection == Path("-")
            else args.projection.open(encoding="utf8")
        )
        with source as handle:
            conversation(
                (SimpleNamespace(**json.loads(line)) for line in handle),
                args.scratch,
                frozen,
            )


if __name__ == "__main__":
    main()
