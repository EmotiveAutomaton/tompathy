"""Explicit offline benchmark commands. No service starts or remote model calls."""
import argparse
import json
from pathlib import Path

from ...admission import implementation_hash
from ...ledger.ids import digest
from ...preview.fixed_backend import FixedQwen
from ...preview.judgments import fixed_reader
from ...preview.readers import LocalReader
from ...transcribe.cache import Cache
from .attention import attention_report, binding_parity, involvement_report, score_sessions
from .data import ReplayMismatch, load_bundle, replay_exports
from .edits import (
    CATEGORIES,
    classifier,
    compare_cascade,
    eligible_edits,
    first_call_projection,
    q8_sample,
    sample_coverage,
    sample_edits,
    scores,
)
from .protocol import PROTOCOL_PIN, receipt
from .reporting import FILES, bind_run, initialize_receipts, public_receipt, save_json, scoreboard
from .resources import benchmark_priority, guard
from .secondary import secondary_report
from .state import finalize


def private_directory(path):
    resolved = Path(path).resolve()
    if not resolved.is_relative_to(Path(".local/bench").resolve()):
        raise ValueError("Private records must stay under ignored .local/bench")
    return resolved


def saved_attention(path):
    directory = private_directory(path)
    report = json.loads((directory/FILES["attention"]).read_text(encoding="utf8"))
    pins = json.loads((directory/"scoring-identity.json").read_text(encoding="utf8"))
    if (report.get("status") != "complete" or report.get("protocol") != PROTOCOL_PIN
            or any(report.get(k) != pins.get(k) for k in ("enginePin","dataPin"))):
        raise ValueError("Training scores require their exact completed EX1 receipt")
    tables = json.loads((directory/"word-scores.json").read_text(encoding="utf8"))
    if pins.get('wordScoresSha256') != digest(tables):
        raise ValueError("Saved word scores differ from their completed run receipt")
    return tables,report,pins


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=["prepare","attention","binding-parity","secondary","edit-features","edit-q8"])
    parser.add_argument("--bundle",type=Path)
    parser.add_argument("--roster",type=Path)
    parser.add_argument("--source-root",type=Path)
    parser.add_argument("--reader",type=Path,default=Path(".local/preview-readers/qwen"))
    parser.add_argument("--smol",type=Path,default=Path(".local/preview-readers/smol"))
    parser.add_argument("--threads",type=int,choices=(1,2),default=1)
    parser.add_argument("--scoring",choices=("window","kv"),default="window")
    parser.add_argument("--precision",choices=("int8","float32"),default="int8")
    parser.add_argument("--private-out",type=Path,default=Path(".local/bench/november-run"))
    parser.add_argument("--receipts",type=Path,default=Path("engine/validation"))
    parser.add_argument("--url",help="Empty dedicated owned loopback Qwen service; never a shared server")
    parser.add_argument("--limit",type=int,choices=(50,1000),default=50,help="Measure and report the first 50 before the rest")
    parser.add_argument("--training-run",type=Path,help="Completed private EX1 run directory")
    parser.add_argument("--comparison-run",type=Path,help="Completed private EX1 run with KV scoring")
    args = parser.parse_args()
    initialize_receipts(args.receipts)
    if args.command == "prepare":
        scoreboard(args.receipts,Path("docs/ENGINE_SCOREBOARD.md"))
        return
    private = private_directory(args.private_out)
    benchmark_priority(args.threads)
    if args.command == "binding-parity":
        if not args.training_run or not args.comparison_run:
            parser.error("Binding parity requires both completed run directories")
        old,_,old_pins = saved_attention(args.training_run)
        new,_,new_pins = saved_attention(args.comparison_run)
        if old_pins['dataPin'] != new_pins['dataPin'] or old_pins['scoring'] != 'window' or new_pins['scoring'] != 'kv':
            raise ValueError("Binding check requires window then KV on identical data")
        value = binding_parity(old,new) | {"windowPin":old_pins,"kvPin":new_pins}
        save_json(args.receipts/"speed-attention-parity-2026-11.json",public_receipt(value))
        return
    if not args.bundle:
        parser.error("Verified bundle required")
    if args.scoring == 'kv' and args.precision != 'float32':
        parser.error("Int8 KV failed TP1 parity; do not run dependent natural-data studies with that configuration")
    manifest,rows = load_bundle(args.bundle,{"attention":"EX1","secondary":"EX4"}.get(args.command,"EX2"))
    excluded = manifest.get('parseFailuresExcluded')
    if args.command == 'secondary' and excluded is not None and (type(excluded) is not int or excluded < 0):
        parser.error("EX4 parse-failure coverage must be an aggregate count")
    roster = None
    if args.command == 'attention':
        if not args.roster or not args.source_root:
            parser.error("Attention requires an explicitly supplied roster and raw source root")
        roster = json.loads(args.roster.read_text(encoding='utf8'))
    data_pin = digest([manifest,roster]) if roster is not None else digest(manifest)
    identity = {"data":data_pin,"implementation":implementation_hash(),"threads":args.threads,
        "scoring":args.scoring,"precision":args.precision}
    if args.command in {'attention','secondary'}:
        identity['readerManifests'] = [digest(json.loads((p/'manifest.json').read_text(encoding='utf8'))) for p in (args.reader,args.smol)]
    bind_run(private,identity)
    if args.command == "attention":
        try:
            sessions,exclusions = replay_exports(rows,roster,args.source_root)
        except ReplayMismatch as error:
            save_json(private/'replay-coverage.json',{'exclusions':error.exclusions,'totalSessions':error.total})
            for capability in ('attention','ai-involvement'):
                report = receipt(capability,status='stopped replay mismatch',data_pin=data_pin)
                report.update(totalSessions=error.total,excludedSessions=len(error.exclusions))
                save_json(args.receipts/FILES[capability],public_receipt(report))
            scoreboard(args.receipts,Path('docs/ENGINE_SCOREBOARD.md'))
            raise
        save_json(private/'replay-coverage.json',{'exclusions':exclusions,'alignment':[{'session':s['session'],**s['alignment']} for s in sessions]})
        guard()
        reader = LocalReader(args.reader,private/"scores",threads=args.threads,precision=args.precision,scoring=args.scoring,entropy=True)
        guard()
        smol = LocalReader(args.smol,private/"scores",threads=args.threads,precision=args.precision,scoring=args.scoring)
        tables = score_sessions(sessions,reader,smol=smol,check=guard)
        save_json(private/"word-scores.json",tables)
        pins = {"engine_pin":digest([implementation_hash(),reader.identity,smol.identity]),"data_pin":data_pin}
        save_json(private/"scoring-identity.json",{"enginePin":pins['engine_pin'],"dataPin":pins['data_pin'],
            "qwen":reader.identity,"smol":smol.identity,"scoring":args.scoring,"wordScoresSha256":digest(tables)})
        for capability,produce in (("attention",attention_report),("ai-involvement",involvement_report)):
            try:
                report = produce(tables,**pins)
            except Exception as error:
                save_json(private/f'{capability}-failure.json',{'error':repr(error)})
                report = receipt(capability,status='stopped analysis',evidence='natural-writing',**pins)
                report['reason'] = type(error).__name__
                save_json(args.receipts/FILES[capability],public_receipt(report))
                scoreboard(args.receipts,Path('docs/ENGINE_SCOREBOARD.md'))
                raise
            report.update(excludedSessions=len(exclusions),alignmentMethods={m:sum(s['alignment']['method'] == m for s in sessions) for m in ('exact-hash','word-length-sequence')})
            save_json(private/FILES[capability],report)
            save_json(args.receipts/FILES[capability],public_receipt(report))
    elif args.command == "secondary":
        if not args.training_run:
            parser.error("EX4 requires the completed EX1 run; its winner cannot be selected on EX4")
        training,primary,pins = saved_attention(args.training_run)
        guard()
        reader = LocalReader(args.reader,private/"scores",threads=args.threads,precision=args.precision,scoring=args.scoring,entropy=True)
        guard()
        smol = LocalReader(args.smol,private/"scores",threads=args.threads,precision=args.precision,scoring=args.scoring)
        if reader.identity != pins['qwen'] or smol.identity != pins['smol']:
            raise ValueError("Secondary check requires the same EX1 reader identities")
        report = secondary_report(training,rows,reader,primary['exploratoryWinner'],smol=smol,check=guard)
        report.update(enginePin=pins['enginePin'],dataPin=digest(manifest),trainingDataPin=pins['dataPin'],
            sourceParseFailuresExcluded=excluded,evidence='natural-writing',productionAdmission=False)
        save_json(private/"secondary.json",report)
        save_json(args.receipts/"attention-secondary-2026-11.json",public_receipt(report))
    else:
        selected,coverage = eligible_edits(rows,manifest["featureNames"])
        probabilities,gates,timings = classifier(selected)
        save_json(private/"edit-features.json",{"rows":selected,"probabilities":probabilities.tolist(),"thresholds":gates,"seconds":timings})
        report = receipt("edit-reasons",status="feature-only; Q8/cascade pending",engine_pin=digest([implementation_hash(),manifest["featureNames"]]),data_pin=digest(manifest),evidence="natural-writing")
        report.update(coverage=coverage,feature=scores([r["category"] for r in selected],[CATEGORIES[int(p.argmax())] for p in probabilities]),
            caveat="Targets are editor comments mapped by frozen keywords; other histories are untested.",thresholds=gates)
        if args.command == "edit-q8":
            if not args.url:
                parser.error("Q8 requires an explicitly owned service URL")
            backend = None
            calls_path = private/"q8-calls.json"
            complete = json.loads(calls_path.read_text(encoding="utf8")) if calls_path.exists() else {}
            projection = private/"q8-first-50.json"
            full_sample = sample_edits(selected)
            indices = full_sample[:args.limit]
            report['sampleCoverage'] = sample_coverage(selected,full_sample)
            report['status'] = 'running Q8 benchmark'
            try:
                guard(large_model=True)
                backend = FixedQwen(args.url,timeout=600,before_load=lambda: guard(large_model=True))
                reader = fixed_reader(backend,Cache(private/"q8.sqlite"))
                if args.limit == 1000 and (not projection.exists() or json.loads(projection.read_text(encoding='utf8')) != first_call_projection(selected,full_sample,complete,reader.pin,data_pin)):
                    raise ValueError("Run and inspect the matching first-50 projection before requesting the rest")
                # Persist each completed bounded call, including before a later failure.
                for index in indices:
                    complete = q8_sample(reader,selected,[index],check=guard,completed=complete)
                    save_json(calls_path,complete)
                    if len(complete) == min(50,len(full_sample)) and not projection.exists():
                        value = first_call_projection(selected,full_sample,complete,reader.pin,data_pin)
                        save_json(projection,value)
                        print(json.dumps(value),flush=True)
                report.update(comparison=compare_cascade(selected,probabilities,gates,timings,complete),
                    status="complete" if len(complete) == len(full_sample) else "pilot-50",readerPin=reader.pin)
                if report['status'] != 'complete':
                    report['comparison'].update(cascadeEligible=False,provisional=True,
                        reason='Initial timing sample only; complete the declared sample before qualification')
            except Exception as error:
                save_json(private/'failure.json',{'error':repr(error),'completedCalls':len(complete)})
                report.update(status='stopped Q8 benchmark',reason=type(error).__name__)
                raise
            finally:
                report['completedCalls'] = len(complete)
                try:
                    finalize(report,args.receipts/FILES['edit-reasons'],backend)
                finally:
                    scoreboard(args.receipts,Path('docs/ENGINE_SCOREBOARD.md'))
        save_json(args.receipts/FILES["edit-reasons"],public_receipt(report))
    scoreboard(args.receipts,Path("docs/ENGINE_SCOREBOARD.md"))


if __name__ == "__main__":
    main()
