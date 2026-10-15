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


def local_reader(config, question_records, cache):
    if not any((config, question_records, cache)):
        return None
    if not all((config, question_records, cache)):
        raise ValueError("Transcription needs config, question records and cache together")
    from .transcribe.backends.local import LocalBackend
    from .transcribe.cache import Cache
    from .transcribe.runner import Transcriber

    records = [read(p) for p in sorted(Path(question_records).glob("*.json"))]
    return Transcriber(LocalBackend(**read(config)), Cache(cache), records)


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
    p.add_argument(
        "--pipeline", action="store_true", help="Fit options, corrections and their joint model"
    )
    p.add_argument("--labels", help="Input-bound literal labels from transcribe")
    p.add_argument("--features", help="Input-bound local embedding/entity features")
    p.add_argument("--questions", default="", help="Comma-separated literal feature questions")
    p.add_argument("--diagnosticity", action="store_true")
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
    p.add_argument(
        "--goals", help="Exact-input goal candidates with a separately pinned producer admission"
    )
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
    p.add_argument("--goals")
    p.add_argument("--history-dir", help="Enable explicit Wikipedia history requests")
    p.add_argument(
        "--questions",
        default="",
        help="Comma-separated admitted history feature questions, such as Q10",
    )
    p.add_argument("--transcriber-config")
    p.add_argument("--question-records")
    p.add_argument("--cache")
    p = commands.add_parser("eval")
    p.add_argument("--dataset", required=True, help="JSON handling records or a ledger directory")
    p.add_argument("--split", choices=["prequential"], default="prequential")
    p.add_argument("--modules", default="backbone,population")
    p.add_argument("--out", required=True)
    p.add_argument("--task", choices=["handling", "options", "corrections"], default="handling")
    p.add_argument("--domain", choices=["writing", "preferences"], default="writing")
    p.add_argument("--until", type=timestamp)
    p.add_argument("--labels")
    p.add_argument("--questions", default="")
    p.add_argument("--heldout-makers", help="JSON list of unseen maker IDs")
    p.add_argument("--features")
    p.add_argument("--heldout-prompts", help="JSON list of unseen prompt IDs")
    p.add_argument("--maximum-targets", type=int, default=1000)
    p = commands.add_parser("eval-source")
    p.add_argument("--ledger", required=True)
    p.add_argument("--until", type=timestamp, required=True)
    p.add_argument("--maximum-targets", type=int, default=1000)
    p.add_argument("--out", required=True)
    p = commands.add_parser("transcribe-test")
    p.add_argument("--config", required=True)
    p.add_argument("--items", required=True)
    p.add_argument("--question", choices=[f"Q{i}" for i in range(1, 11)], required=True)
    p.add_argument("--cache", required=True)
    p.add_argument("--out", required=True)
    p = commands.add_parser("battery-build")
    p.add_argument("--question", choices=[f"Q{i}" for i in range(1, 11)], required=True)
    p.add_argument("--entity-model")
    p.add_argument("--out", required=True)
    p = commands.add_parser("transcribe")
    p.add_argument("--ledger", required=True)
    p.add_argument("--domain", choices=["writing", "preferences"], default="writing")
    p.add_argument("--until", type=timestamp, required=True)
    p.add_argument("--config", required=True)
    p.add_argument("--question-records", required=True)
    p.add_argument("--questions", default="Q8,Q9")
    p.add_argument("--maximum-calls", type=int, default=500)
    p.add_argument("--cache", required=True)
    p.add_argument("--out", required=True)
    p = commands.add_parser("interface")
    p.add_argument("--out", required=True)
    p = commands.add_parser("native-panel")
    p.add_argument("--manifest", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--ledger", help="Optionally ingest the converted exchange")
    p = commands.add_parser("calibrate")
    p.add_argument("--source", required=True)
    p.add_argument(
        "--method",
        choices=["temperature", "prior-shift", "contextual", "stacking"],
        default="temperature",
    )
    p.add_argument("--out", required=True)
    p = commands.add_parser("goals-build")
    p.add_argument("--capture", required=True)
    p.add_argument("--ledger")
    p.add_argument("--maker", required=True, help="Exact source-scoped packet maker ID")
    p.add_argument("--config", required=True)
    p.add_argument("--cache", required=True)
    p.add_argument("--maximum-calls", type=int, default=21)
    p.add_argument("--root-reliability", type=float, default=0)
    p.add_argument("--out", required=True)
    p = commands.add_parser("fit-posterior")
    p.add_argument("--ledger", required=True)
    p.add_argument("--domain", choices=["writing", "preferences"], default="writing")
    p.add_argument("--task", choices=["options", "corrections", "joint"], default="options")
    p.add_argument("--until", type=timestamp, required=True)
    p.add_argument("--labels")
    p.add_argument("--features")
    p.add_argument("--questions", default="")
    p.add_argument("--method", choices=["nuts", "svi"], default="nuts")
    p.add_argument("--warmup", type=int, default=300)
    p.add_argument("--samples", type=int, default=500)
    p.add_argument("--steps", type=int, default=2000)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--maximum-records", type=int, default=10000)
    p.add_argument("--out", required=True)
    p = commands.add_parser("features")
    p.add_argument("--ledger", required=True)
    p.add_argument("--domain", choices=["writing", "preferences"], default="writing")
    p.add_argument("--until", type=timestamp, required=True)
    p.add_argument("--embedding-model")
    p.add_argument("--entity-model")
    p.add_argument("--cache", required=True)
    p.add_argument("--maximum", type=int, default=10000)
    p.add_argument("--out", required=True)
    p = commands.add_parser("ghost-ingest")
    p.add_argument("--source", required=True)
    p.add_argument("--ledger", required=True)
    p = commands.add_parser("analyze-history")
    p.add_argument("--capture", required=True)
    p.add_argument("--directory", required=True)
    p.add_argument("--source", help="Normalized history JSON; omit to fetch Wikipedia")
    p.add_argument("--adapter", choices=["wikipedia", "git"], default="wikipedia")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--maximum-calls", type=int, default=500)
    p.add_argument("--admissions")
    p.add_argument("--config")
    p.add_argument("--question-records")
    p.add_argument("--cache")
    p.add_argument("--questions", default="")
    p.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "ingest":
            result = ingest(args)
            if args.out:
                write(args.out, result)
        elif args.command == "fit":
            from .models.bundle import fit_bundle

            if args.pipeline:
                from .features.augment import Features
                from .features.records import Labels
                from .models.pipeline import fit_pipeline

                if args.task != "options":
                    raise ValueError("The text pipeline does not fit handling indicators")
                model = fit_pipeline(
                    Ledger(args.ledger),
                    population=args.population,
                    until=args.until,
                    labels=Labels.model_validate(read(args.labels)) if args.labels else None,
                    extra_features=Features.model_validate(read(args.features))
                    if args.features
                    else None,
                    questions=[q for q in args.questions.split(",") if q],
                    diagnosticity=args.diagnosticity,
                )
            else:
                if args.labels or args.questions or args.diagnosticity or args.features:
                    raise ValueError("Literal/correction/diagnosticity features require --pipeline")
                model = fit_bundle(
                    Ledger(args.ledger),
                    population=args.population,
                    until=args.until,
                    task=args.task,
                )
            result = model.model_dump(mode="json")
            target = args.out or str(Path(args.ledger) / "models" / (args.population + ".json"))
            write(target, result)
            result = {
                "model": target,
                "trainingComparisons": {k: len(v.train_ids) for k, v in model.fits.items()}
                if args.pipeline
                else len(model.train_ids),
            }
        elif args.command == "analyze":
            from .models.bundle import load_bundle
            from .models.goals import GoalInputs
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
                goals=GoalInputs.model_validate(read(args.goals)) if args.goals else None,
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
            from .models.goals import GoalInputs
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
                goals=GoalInputs.model_validate(read(args.goals)) if args.goals else None,
                history_dir=args.history_dir,
                history_questions=[q for q in args.questions.split(",") if q],
                reader=local_reader(args.transcriber_config, args.question_records, args.cache),
            )
            uvicorn.run(app, host="127.0.0.1", port=args.port, access_log=False)
            return
        elif args.command == "eval-source":
            from .eval.harness import write_scores
            from .eval.source import evaluate

            scores, result = evaluate(
                Ledger(args.ledger), until=args.until, maximum_targets=args.maximum_targets
            )
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            write_scores(scores, args.out)
            write(str(args.out) + ".receipt.json", result)
        elif args.command == "eval":
            from .eval.harness import handling_prequential, write_scores
            from .eval.ledger import handling_records

            selected = set(args.modules.split(","))
            if args.task != "handling":
                from .eval.pipeline import evaluate
                from .features.augment import Features
                from .features.records import Labels

                if args.until is None:
                    raise ValueError("Module evaluation requires --until")
                scores, result = evaluate(
                    Ledger(args.dataset),
                    domain=args.domain,
                    until=args.until,
                    labels=Labels.model_validate(read(args.labels)) if args.labels else None,
                    extra_features=Features.model_validate(read(args.features))
                    if args.features
                    else None,
                    questions=[q for q in args.questions.split(",") if q],
                    modules=sorted(selected),
                    task=args.task,
                    heldout_makers=read(args.heldout_makers) if args.heldout_makers else (),
                    heldout_prompts=read(args.heldout_prompts) if args.heldout_prompts else (),
                    maximum_targets=args.maximum_targets,
                )
                Path(args.out).parent.mkdir(parents=True, exist_ok=True)
                write_scores(scores, args.out)
                write(str(args.out) + ".receipt.json", result)
                print(json.dumps(result, indent=2))
                return
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
        elif args.command == "features":
            from .features.augment import extract

            result = extract(
                Ledger(args.ledger),
                domain=args.domain,
                until=args.until,
                cache_directory=args.cache,
                embedding_model=args.embedding_model,
                entity_model=args.entity_model,
                maximum=args.maximum,
            )
            write(args.out, result.model_dump(mode="json"))
            result = {"subjects": len(result.rows), "model_pins": result.model_pins}
        elif args.command == "fit-posterior":
            from .features.augment import Features
            from .features.records import Labels
            from .models.bayesian import fit
            from .models.pipeline import cases

            options, corrections, _, _ = cases(
                Ledger(args.ledger).snapshot(),
                domain=args.domain,
                until=args.until,
                labels=Labels.model_validate(read(args.labels)) if args.labels else None,
                extra_features=Features.model_validate(read(args.features))
                if args.features
                else None,
                questions=[q for q in args.questions.split(",") if q],
            )
            rows = {"options": options, "corrections": corrections, "joint": options + corrections}[
                args.task
            ]
            result = fit(
                rows,
                until=args.until,
                method=args.method,
                warmup=args.warmup,
                samples=args.samples,
                steps=args.steps,
                seed=args.seed,
                maximum_records=args.maximum_records,
            )
            write(args.out, result)
        elif args.command == "battery-build":
            from .transcribe.batteries import constructed

            items = constructed(args.question, entity_model=args.entity_model)
            write(args.out, items)
            result = {
                "items": len(items),
                "source": "constructed writing; not natural-data validation",
            }
        elif args.command == "goals-build":
            from .models.goal_producer import produce
            from .transcribe.backends.local import LocalBackend
            from .transcribe.cache import Cache

            result = produce(
                read(args.capture),
                Ledger(args.ledger).snapshot() if args.ledger else None,
                LocalBackend(**read(args.config)),
                Cache(args.cache),
                maker=args.maker,
                maximum_calls=args.maximum_calls,
                root_reliability=args.root_reliability,
            )
            write(args.out, result.model_dump(mode="json"))
            result = {
                "candidates": len(result.candidates),
                "generator_pin": result.generator_pin,
                "admission": "requires separate goal-candidates and goal-tree gates",
            }
        elif args.command == "calibrate":
            from .models.calibration_record import calibrate

            result = calibrate(read(args.source), method=args.method)
            write(args.out, result)
        elif args.command == "native-panel":
            from .adapters.native_panel import from_manifest
            from .adapters.panel import ingest as ingest_panel

            exchange, result = from_manifest(args.manifest)
            write(args.out, exchange)
            if args.ledger:
                result["ledger"] = ingest_panel(exchange, Ledger(args.ledger))
            write(str(args.out) + ".receipt.json", result)
        elif args.command == "interface":
            from .interface import contract

            result = contract()
            write(args.out, result)
            result = {"interface": args.out, "implementation": result["implementation_hash"]}
        elif args.command == "ghost-ingest":
            from .ghost.bridge import ingest_reader

            result = ingest_reader(args.source, Ledger(args.ledger))
        elif args.command == "analyze-history":
            from .workflow import analyze_history

            packet, result = analyze_history(
                read(args.capture),
                directory=args.directory,
                admissions=Admissions.load(Path(args.admissions) if args.admissions else None),
                reader=local_reader(args.config, args.question_records, args.cache),
                questions=[q for q in args.questions.split(",") if q],
                limit=args.limit,
                maximum_calls=args.maximum_calls,
                payload=read(args.source) if args.source else None,
                adapter=args.adapter,
            )
            write(args.out, packet)
            write(str(args.out) + ".receipt.json", result)
        elif args.command == "transcribe":
            from .features.records import transcribe
            from .transcribe.backends.local import LocalBackend
            from .transcribe.cache import Cache
            from .transcribe.runner import Transcriber

            records = [read(p) for p in sorted(Path(args.question_records).glob("*.json"))]
            reader = Transcriber(LocalBackend(**read(args.config)), Cache(args.cache), records)
            result = transcribe(
                Ledger(args.ledger).snapshot(),
                reader,
                domain=args.domain,
                until=args.until,
                questions=args.questions.split(","),
                maximum=args.maximum_calls,
            )
            write(args.out, result.model_dump(mode="json"))
            result = {"labels": args.out, "subjects": len(result.labels)}
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
