"""Bounded EX3 runner. Reads exact Git objects; never changes either checkout."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from time import monotonic

from ...admission import implementation_hash
from ...ledger.ids import digest
from ...preview.fixed_backend import FixedQwen
from ...preview.readers import LocalReader
from ...transcribe.cache import Cache
from .data import load_bundle
from .goals import pilot_document, pilot_inputs, pilot_sample, pilot_summary
from .protocol import receipt
from .reporting import bind_run, initialize_receipts, public_receipt, save_json, scoreboard
from .resources import benchmark_priority, guard
from .state import PilotDeadline, finalize


def pinned_document(task, roots):
    commit,path = task["commit"],task["path"]
    if not re.fullmatch(r"[a-f0-9]{40}",commit) or Path(path).is_absolute() or ".." in Path(path).parts or ":" in path or "\\" in path:
        raise ValueError("Invalid pinned repository reference")
    root = Path(roots[task["repository"]]).resolve()
    raw = subprocess.run(["git","-C",str(root),"show",f"{commit}:{path}"],check=True,capture_output=True,timeout=30).stdout
    if hashlib.sha256(raw).hexdigest() != task["sha256"]:
        raise ValueError("Pinned document digest mismatch")
    return raw.decode("utf8")


def materialize(task, lookup, roots, check=lambda:None):
    ids = [task["id"],*task["distractors"]]
    if len(ids) != 50 or len(set(ids)) != 50:
        raise ValueError("EX3 task needs 49 fixed distractors")
    candidates = []
    for ident in ids:
        check()
        record = lookup[ident]
        text = pinned_document(record,roots)
        sections = [s for s in record["sections"] if s["kind"].casefold() == "motivation"]
        if len(sections) != 1:
            raise ValueError("Exactly one Motivation section required")
        section = sections[0]
        start,end = section["contentStart"],section["end"]
        if not section["start"] <= start < end <= len(text):
            raise ValueError("Invalid Motivation content offsets")
        candidates.append({"id":ident,"text":text[start:end]})
    return task | {"candidates":candidates,"truth":task["id"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle",type=Path,required=True)
    parser.add_argument("--peps",type=Path,required=True)
    parser.add_argument("--eips",type=Path,required=True)
    parser.add_argument("--url",required=True,help="Explicit empty dedicated loopback service owned by this run")
    parser.add_argument("--reader",type=Path,default=Path('.local/preview-readers/qwen'))
    parser.add_argument("--private-out",type=Path,default=Path('.local/bench/goal-pilot'))
    parser.add_argument("--out",type=Path,default=Path('engine/validation/goals-motivation-pilot-2026-11.json'))
    args = parser.parse_args()
    if not args.private_out.resolve().is_relative_to(Path('.local/bench').resolve()):
        parser.error("Private outcomes must stay under .local/bench")
    manifest,tasks = load_bundle(args.bundle,"EX3")
    lookup = {t['id']:t for t in tasks}
    if len(lookup) != len(tasks):
        raise ValueError("Duplicate EX3 document")
    selected = pilot_sample(tasks)
    roots = {'peps':args.peps,'eips':args.eips}
    bind_run(args.private_out,{"kind":"EX3","manifest":digest(manifest),"implementation":implementation_hash(),
        "readerManifest":digest(json.loads((args.reader/'manifest.json').read_text(encoding='utf8')))})
    benchmark_priority(1)
    initialize_receipts(args.out.parent)
    deadline = PilotDeadline(args.private_out/'deadline.json')
    backend = None
    cache = Cache(args.private_out/'goals.sqlite')
    start,paired = monotonic(),[]
    progress_path = args.private_out/'documents.json'
    documents = json.loads(progress_path.read_text(encoding='utf8')) if progress_path.exists() else {}
    report = receipt('goals',status='running pilot',data_pin=digest(manifest),evidence='natural-writing')
    report['budget'] = deadline.state
    def check():
        guard()
        deadline.check()
    try:
        deadline.check()
        guard(large_model=True)
        reader = LocalReader(args.reader,args.private_out/'scores')
        guard(large_model=True)
        backend = FixedQwen(args.url,timeout=600,before_load=lambda: guard(large_model=True))
        report['enginePin'] = digest([implementation_hash(),backend.model_id,backend.settings,reader.identity])
        for task in selected:
            check()
            document = pinned_document(task,roots)
            inputs,cues = pilot_inputs(document,task['sections'],task['title'],task['headings'],reader,check)
            def progress(value):
                documents[value['id']] = value
                save_json(progress_path,documents)
            completed = pilot_document(materialize(task,lookup,roots,check),inputs,cues,backend,cache,check=check,
                completed=documents.get(task['id']),on_progress=progress)
            paired.append(completed)
            save_json(args.private_out/'paired.json',paired)
            report['completedDocuments'] = len(paired)
            save_json(args.out,public_receipt(report))
        report['status'] = 'complete pilot'
    except Exception as exc:
        save_json(args.private_out/'failure.json',{'error':repr(exc),'completedDocuments':len(paired)})
        report.update(status='stopped pilot',reason=type(exc).__name__,details='See private failure receipt; raw model output stays local')
        raise
    finally:
        try:
            paired = [documents[t['id']] for t in selected if t['id'] in documents and set(documents[t['id']]['readers']) == {'body','departures','cues-only'}]
            report['completedDocuments'] = len(paired)
            if len({p['author'] for p in paired}) >= 2:
                report['pilot'] = pilot_summary(paired)
        finally:
            report['elapsedSeconds'] = monotonic()-start
            try:
                finalize(report,args.out,backend)
            finally:
                scoreboard(args.out.parent,Path('docs/ENGINE_SCOREBOARD.md'))


if __name__ == '__main__':
    main()
