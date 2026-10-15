"""Local engine commands. Registry publish writes files; it never deploys."""

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path

from .admission import Admissions
from .ledger.ids import canonical
from .ledger.store import Ledger


def read(path):
    return json.loads(Path(path).read_text(encoding="utf8"))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical(value) + b"\n")


def timestamp(value):
    result = datetime.fromisoformat(value)
    if result.tzinfo is None:
        raise argparse.ArgumentTypeError("Timestamp must include its timezone")
    return result


def ingest(args):
    ledger = Ledger(args.ledger)
    if args.adapter == "lichess":
        from .adapters.lichess import ingest as compile_pgn

        return compile_pgn(Path(args.source).read_text(encoding="utf8"), ledger)
    if args.adapter == "wiki" and args.source.startswith("https://"):
        from .adapters.wiki import fetch_history
        from .adapters.wiki import ingest as compile_wiki

        if not args.artifact:
            raise ValueError("Live history requires --artifact from the exact capture")
        return compile_wiki(
            fetch_history(args.source, artifact_id=args.artifact, limit=args.limit), ledger
        )
    payload = read(args.source)
    if args.adapter == "coauthor":
        from .adapters.coauthor import compile_session

        root = Path(args.source).resolve().parent
        path = (root / payload["events_file"]).resolve()
        if not path.is_relative_to(root):
            raise ValueError("CoAuthor event path escapes the declared source bundle")
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != payload["source_sha256"]:
            raise ValueError("CoAuthor source pin mismatch")
        events = [json.loads(line) for line in raw.decode("utf8").splitlines()]
        rows, provenance, excluded = compile_session(
            events,
            source_id=payload["source_id"],
            writer=payload["writer"],
            prompt=payload.get("prompt"),
            prompt_id=payload.get("prompt_id"),
            source_hash=payload["source_sha256"],
            ledger=ledger,
        )
        ledger.append_new(rows, provenance)
        return {"records": len(rows), "excluded": excluded}
    from importlib import import_module

    return import_module(".adapters." + args.adapter, __package__).ingest(payload, ledger)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="tompathy-engine")
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("ingest")
    p.add_argument(
        "--adapter",
        choices=["capture", "coauthor", "git", "wiki", "lichess", "panel"],
        required=True,
    )
    p.add_argument("--source", required=True)
    p.add_argument("--ledger", required=True)
    p.add_argument("--artifact")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--out")
    p = commands.add_parser("fit")
    p.add_argument("--ledger", required=True)
    p.add_argument(
        "--population", choices=["writing-v0", "preferences-v0", "chess-v0"], required=True
    )
    p.add_argument("--until", type=timestamp, required=True)
    p.add_argument("--task", choices=["options", "handling"], default="options")
    p.add_argument("--out")
    p = commands.add_parser("analyze")
    p.add_argument("--ledger")
    p.add_argument("--artifact", required=True)
    p.add_argument("--capture", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--admissions")
    p.add_argument(
        "--model",
        help="Pinned model JSON from fit; needs scientific admission to contribute estimates",
    )
    p.add_argument("--context")
    p = commands.add_parser("population")
    p.add_argument("action", choices=["build"])
    p.add_argument("--ledger", required=True)
    p.add_argument("--id", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--until", type=timestamp)
    p = commands.add_parser("registry")
    p.add_argument("action", choices=["publish"])
    p.add_argument("--packets", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--private", action="store_true")
    p = commands.add_parser("serve")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--token-file", type=Path, required=True)
    p.add_argument("--extension-origin", action="append", default=[])
    p.add_argument("--ledger")
    p.add_argument("--admissions")
    p.add_argument("--population-dir")
    p.add_argument("--model")
    p = commands.add_parser("eval")
    p.add_argument("--dataset", required=True, help="JSON handling records or a ledger directory")
    p.add_argument("--split", choices=["prequential"], default="prequential")
    p.add_argument("--modules", default="backbone,population")
    p.add_argument("--out", required=True)
    p = commands.add_parser("transcribe-test")
    p.add_argument("--config", required=True)
    p.add_argument("--items", required=True)
    p.add_argument("--question", choices=[f"Q{i}" for i in range(1, 11)], required=True)
    p.add_argument("--cache", required=True)
    p.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "ingest":
            result = ingest(args)
            if args.out:
                write(args.out, result)
        elif args.command == "fit":
            from .models.bundle import fit_bundle

            model = fit_bundle(
                Ledger(args.ledger), population=args.population, until=args.until, task=args.task
            )
            result = model.model_dump(mode="json")
            target = args.out or str(Path(args.ledger) / "models" / (args.population + ".json"))
            write(target, result)
            result = {"model": target, "trainingDecisions": len(model.train_ids)}
        elif args.command == "analyze":
            from .models.bundle import load_bundle
            from .packet.build import build_packet

            capture = read(args.capture)
            if capture["id"] != args.artifact:
                raise ValueError("Requested artifact differs from the capture")
            result = build_packet(
                capture,
                ledger=Ledger(args.ledger) if args.ledger else None,
                context=read(args.context) if args.context else (),
                scope="context" if args.context else "artifact",
                admissions=Admissions.load(Path(args.admissions) if args.admissions else None),
                model=load_bundle(args.model),
            )
            write(args.out, result)
            result = {"packet": args.out, "hypotheses": len(result["hypotheses"])}
        elif args.command == "population":
            from .population.build import build

            result = build(Ledger(args.ledger), args.id, until=args.until)
            write(args.out, result)
        elif args.command == "registry":
            from .registry.publish import from_directory

            result = from_directory(args.packets, args.out, private=args.private)
        elif args.command == "serve":
            import uvicorn

            from .models.bundle import load_bundle
            from .serve.app import create_app, load_token

            if not 1024 <= args.port <= 65535:
                raise ValueError("Choose a port between 1024 and 65535")
            app = create_app(
                token=load_token(args.token_file),
                origins=args.extension_origin,
                ledger_path=args.ledger,
                admissions=Admissions.load(Path(args.admissions) if args.admissions else None),
                population_dir=args.population_dir,
                model=load_bundle(args.model),
            )
            uvicorn.run(app, host="127.0.0.1", port=args.port, access_log=False)
            return
        elif args.command == "eval":
            from .eval.harness import handling_prequential, write_scores
            from .eval.ledger import handling_records

            selected = set(args.modules.split(","))
            if not selected or not selected <= {"backbone", "population"}:
                raise ValueError(
                    "This handling evaluator supports backbone,population; evaluate other modules through their declared task harness"
                )
            rows = (
                handling_records(Ledger(args.dataset))
                if Path(args.dataset).is_dir()
                else read(args.dataset)
            )
            scores, result = handling_prequential(
                rows, progress=lambda p: print(json.dumps(p), flush=True)
            )
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            write_scores([r for r in scores if r["module"] in selected], args.out)
            write(str(args.out) + ".receipt.json", result)
        else:
            from .transcribe.admission import battery
            from .transcribe.backends.local import LocalBackend
            from .transcribe.cache import Cache
            from .transcribe.runner import Transcriber

            reader = Transcriber(LocalBackend(**read(args.config)), Cache(args.cache))
            result = battery(reader, args.question, read(args.items))
            write(args.out, result)
            result = {k: v for k, v in result.items() if k != "outcomes"}
        print(json.dumps(result, indent=2))
    except (ValueError, KeyError, OSError, RuntimeError) as exc:
        parser.exit(2, f"Engine refused the operation: {exc}\n")


if __name__ == "__main__":
    main()
