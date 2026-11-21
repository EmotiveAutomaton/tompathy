"""Explicit preflight reproduction under the existing counted CPU protocol."""
import argparse
import hashlib
import importlib.util
import json
import runpy
import shutil
import sys
import time
from contextlib import redirect_stdout
from datetime import UTC, datetime, timedelta
from pathlib import Path


def heartbeat(output, deadline, headroom):
    """Bound transient Windows replacement contention without weakening guards."""
    from tompathy_engine.eval.back_half.reporting import save_json
    for attempt in range(6):
        if time.monotonic() >= deadline or (output/'STOP').exists():
            raise RuntimeError('Preflight bounded deadline or requested stop')
        value = {'at': datetime.now(UTC).isoformat(), **headroom()}
        try:
            save_json(output/'heartbeat.json', value)
            return
        except PermissionError as exc:
            if getattr(exc, 'winerror', None) not in (5, 32, 33) or attempt == 5:
                raise
            time.sleep(.05 * 2**attempt)


def remaining_seconds(hours, resume, card, now):
    seconds = hours * 3600
    if resume is not None and card in {'TP15', 'TP16', 'TP19'}:
        read = lambda name: json.loads((resume/name).read_text(encoding='utf8'))
        plan = read('plan.json')
        deadline = (datetime.fromisoformat(plan['deadlineAt']) if plan.get('deadlineAt') else
                    datetime.fromisoformat(read('owner.json')['at']) + timedelta(hours=plan['hours']))
        seconds = min(seconds, (deadline - now).total_seconds())
    if seconds <= 0:
        raise ValueError('Original job deadline has expired; no fresh retry clock')
    return seconds


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sounding-line', type=Path, required=True)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--corpus', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--checks', nargs='+', choices=['pf_a', 'pf_b', 'pf_c', 'pf_c2',
        'pf_d', 'pf_e', 'pf_f', 'pf_g', 'pf_h', 'pf_i'], default=[])
    parser.add_argument('--card', choices=['TP10', 'TP12', 'TP12-L3', 'TP10-L3', 'TP11', 'TP13', 'TP14', 'TP15', 'TP16', 'TP17', 'TP18', 'TP18-probe', 'TP19', 'TP20', 'TP22', 'TP1c', 'TP4-controls', 'TP26', 'TP7', 'TP23', 'TP24', 'TP24-mixed', 'TP24-chat', 'TP25', 'TP27', 'TP28', 'TP29', 'TP30-frozen', 'TP32', 'TP33', 'G2-first-rungs', 'G2-modernbert', 'TP34', 'TP35', 'TP36', 'TP37', 'TP38', 'RD1', 'RD2', 'TP12-gated', 'TP22-gated', 'TS3-real', 'TRIGGER-export'])
    parser.add_argument('--models', type=Path, default=Path('.local/readers/models'))
    parser.add_argument('--prepared', type=Path, default=Path('.local/bench/two-day-prepared'))
    parser.add_argument('--ladder', type=Path)
    parser.add_argument('--twins', type=Path)
    parser.add_argument('--ed', type=Path, default=Path('.local/readers/data/empathetic-dialogues'))
    parser.add_argument('--motive-head', type=Path, default=Path('.local/readers/motive-head'))
    parser.add_argument('--reader-job', type=Path)
    parser.add_argument('--counting', type=Path, default=Path('.local/readers/tp12-a'))
    parser.add_argument('--go', type=Path, default=Path('.local/readers/data/go-emotions'))
    parser.add_argument('--rated-data', type=Path)
    parser.add_argument('--casino', type=Path, default=Path('.local/readers/data/casino'))
    parser.add_argument('--emocause', type=Path, default=Path('.local/readers/data/emocause'))
    parser.add_argument('--coverage-job', type=Path)
    parser.add_argument('--goal-baseline', type=Path, default=Path('.local/bench/two-day-tp4-tfidf'))
    parser.add_argument('--primary-job', type=Path)
    parser.add_argument('--preflight-decision', type=Path, help='Explicit source-bound TP23 table-scope ruling')
    parser.add_argument('--ledger', type=Path)
    parser.add_argument('--source-config', type=Path, default=Path('.local/bench/two-day-input-config.json'))
    parser.add_argument('--motive-job', type=Path)
    parser.add_argument('--blogs', type=Path, default=Path('.local/readers/data/blogs-b'))
    parser.add_argument('--smol', type=Path, default=Path('.local/preview-readers/smol'))
    parser.add_argument('--converter', type=Path, default=Path('.local/bench/weightonly'))
    parser.add_argument('--speed-texts', type=Path, default=Path('.local/bench/speed-texts-20261111.json'))
    parser.add_argument('--intake', type=Path, default=Path('.local/bench/two-day-ex1-intake'))
    parser.add_argument('--attention-source', type=Path, default=Path('.local/bench/two-day-20261113-b'))
    parser.add_argument('--resume', type=Path, help='Verified unfinished TP10, rated or TP19 engineering failure/host restart')
    parser.add_argument('--hours', type=float, default=2)
    parser.add_argument('--deadline-at', help='Retain an original UTC deadline for a bounded engineering retry')
    parser.add_argument('--rung', choices=['bow', 'frozen', 'fine', 'base'], default='bow')
    parser.add_argument('--seed', type=int, choices=[23,47,71], default=23)
    parser.add_argument('--fold', type=int, choices=range(5))
    parser.add_argument('--fold-jobs', type=Path, nargs=5, default=[])
    parser.add_argument('--gate-job', type=Path)
    parser.add_argument('--needs-job', type=Path)
    parser.add_argument('--packs', type=Path, nargs='+', default=[])
    parser.add_argument('--vector-cache', type=Path)
    parser.add_argument('--vector-source', type=Path)
    parser.add_argument('--export-kind', choices=['worry','need','gate','label','trigger','counting'])
    parser.add_argument('--tag-map-version', type=int, choices=(1, 2), default=1)
    parser.add_argument('--ledger-row', help='Preassigned public result ledger ID for the new commission')
    parser.add_argument('--study-protocol', type=Path, help='Frozen new-card implementation protocol')
    parser.add_argument('--rung-jobs', type=Path, nargs='+', default=[])
    parser.add_argument('--gate-pack', type=Path)
    parser.add_argument('--need-pack', type=Path)
    parser.add_argument('--label-pack', type=Path)
    parser.add_argument('--inputs', type=Path, help='Verified preceding pf_b output for counting checks')
    args = parser.parse_args()
    if bool(args.checks) == bool(args.card):
        parser.error('Choose either supplied preflight checks or one reader card')
    if args.resume is not None and args.card not in {'TP10','TP15','TP16','TP19'}:
        parser.error('This card has no reviewed engineering continuation yet; preserve the failure and original clock before implementing one')
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    if not output.is_relative_to(root / '.local') or not 0 < args.hours <= 8:
        parser.error('Private fresh output and a bounded 0–8 hour job required')
    if args.vector_cache is not None and not args.vector_cache.resolve().is_relative_to(root/'.local'):
        parser.error('Shared vectors must remain private')
    if args.preflight_decision is not None and not (args.card == 'TP23' and args.rung != 'bow' or args.card == 'TRIGGER-export' and args.export_kind == 'need'):
        parser.error('A TP23 preflight decision only applies to later need rungs and need selection')
    started = datetime.now(UTC)
    seconds = remaining_seconds(args.hours, args.resume, args.card, started)
    if args.deadline_at is not None:
        original_deadline = datetime.fromisoformat(args.deadline_at)
        if original_deadline.tzinfo is None:
            parser.error('Retry deadline must include its timezone')
        seconds = min(seconds, (original_deadline-started).total_seconds())
        if seconds <= 0:
            parser.error('Original retry deadline has expired')
    deadline = time.monotonic() + seconds
    output.mkdir(parents=True, exist_ok=False)
    if args.inputs:
        if not (args.inputs/'exit-verification.json').exists():
            parser.error('Preceding reproduction needs verified exit')
        for name in ('test_ids.csv', 'tfidf_proba.npy'):
            (output/name).write_bytes((args.inputs/name).read_bytes())
    snapshot = output/'code'
    shutil.copytree(root/'engine/tompathy_engine', snapshot/'tompathy_engine',
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    sys.path.insert(0, str(snapshot))
    from tompathy_engine.eval.back_half.reporting import save_json
    from tompathy_engine.eval.back_half.resources import benchmark_priority, guard
    benchmark_priority(2)
    spec = importlib.util.spec_from_file_location('counted', root/'scripts/engine-two-day-job.py')
    counted = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(counted)
    scripts = {n: (args.bundle / 'corpus/scripts' / (n + '.py')).resolve() for n in args.checks}
    hashes = {n: hashlib.sha256(p.read_bytes()).hexdigest() for n, p in scripts.items()}
    auxiliary = {}
    if args.study_protocol is not None:
        name = 'study-protocol.md'
        payload = args.study_protocol.read_bytes()
        (output/name).write_bytes(payload)
        auxiliary[name] = hashlib.sha256(payload).hexdigest()
        args.study_protocol = output/name
    if args.preflight_decision is not None:
        name = 'preflight-decision.json'
        payload = args.preflight_decision.read_bytes()
        (output/name).write_bytes(payload)
        auxiliary[name] = hashlib.sha256(payload).hexdigest()
        args.preflight_decision = output/name
    if 'pf_e' in args.checks:
        name = 'twin_predictions_written_before_numbers.json'
        source = args.bundle/'corpus/out'/name
        payload = source.read_bytes()
        (output/name).write_bytes(payload)
        auxiliary[name] = hashlib.sha256(payload).hexdigest()
    next_check = 0.

    def check():
        heartbeat(output, deadline, guard)

    def trace(frame, event, arg):
        nonlocal next_check
        if event == 'line' and time.monotonic() >= next_check:
            next_check = time.monotonic() + 5
            check()
        return trace if frame.f_code.co_filename in source_paths else None

    source_paths = {str(p) for p in scripts.values()}
    save_json(output/'plan.json', {'scripts': hashes, 'auxiliaryInputs': auxiliary, 'corpus': str(args.corpus.resolve()),
        'threads': 2, 'hours': args.hours, 'card': args.card,
        'deadlineAt': (started + timedelta(seconds=seconds)).isoformat(),
        'snapshotFiles': {p.relative_to(snapshot).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in snapshot.rglob('*') if p.is_file() and '__pycache__' not in p.parts},
        'status': 'benchmark only; no admission',
        'launcherSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    completed = []
    try:
        with counted.lease(args.sounding_line, output, card='ToMpathy-readers-preflight-20261115'):
            check()
            # No import can create additional BLAS workers beyond this allowance.
            from threadpoolctl import threadpool_limits
            with threadpool_limits(limits=2):
                if args.card == 'TRIGGER-export':
                    from tompathy_engine.eval.readers.trigger_export import run_export
                    run_export(args.export_kind,args,output,check)
                    completed.append('TRIGGER export '+args.export_kind)
                elif args.card == 'TP34':
                    from tompathy_engine.eval.readers.tp34 import run
                    if not args.ledger_row or not args.study_protocol or not args.primary_job:
                        raise ValueError('TP34 requires its frozen source, protocol and ledger identity')
                    run(args.primary_job,args.ed,args.go,output,check,args.ledger_row,args.study_protocol)
                    completed.append('TP34')
                elif args.card == 'TP35':
                    from tompathy_engine.eval.readers.tp35 import run
                    if not args.ledger_row or not args.study_protocol:
                        raise ValueError('TP35 requires its protocol and ledger identity')
                    run(args.corpus,output,check,args.ledger_row,args.study_protocol)
                    completed.append('TP35')
                elif args.card == 'TP24-chat':
                    from tompathy_engine.eval.readers.tp24_chat import run
                    if not all((args.rated_data,args.primary_job,args.needs_job,args.coverage_job,args.inputs,
                                args.ledger_row,args.study_protocol)):
                        raise ValueError('TP24 chat requires the owner boundary, three filed sources and protocol')
                    run(args.rated_data,args.ed,args.primary_job,args.needs_job,args.coverage_job,args.inputs,
                        output,check,args.ledger_row,args.study_protocol)
                    completed.append('TP24-chat')
                elif args.card in ('G2-first-rungs','G2-modernbert'):
                    from tompathy_engine.eval.readers.word_ladder import run
                    if not all((args.primary_job,args.coverage_job,args.rated_data,args.ledger_row,args.study_protocol)):
                        raise ValueError('G2 ladder needs its frozen job, verified mirror, prepared inputs and protocol')
                    run(args.primary_job,args.coverage_job,args.rated_data,output,check,args.ledger_row,args.study_protocol,
                        modernbert=args.card=='G2-modernbert')
                    completed.append(args.card)
                elif args.card == 'TP33':
                    from tompathy_engine.eval.readers.tp33 import run
                    if not all((args.primary_job,args.rated_data,args.ledger_row,args.study_protocol)):
                        raise ValueError('TP33 requires both verified source jobs, protocol and ledger identity')
                    run(args.primary_job,args.rated_data,output,check,args.ledger_row,args.study_protocol)
                    completed.append('TP33')
                elif args.card == 'TP32':
                    from tompathy_engine.eval.readers.tp32 import run
                    if not args.ledger_row or not args.study_protocol:
                        raise ValueError('TP32 requires its protocol and ledger identity')
                    run(args.source_config,args.models,output,check,args.ledger_row,args.study_protocol)
                    completed.append('TP32')
                elif args.card == 'TP37':
                    from tompathy_engine.eval.readers.tp37 import run
                    if not args.ledger_row or not args.study_protocol:
                        raise ValueError('TP37 requires its registered protocol and ledger identity')
                    run(args.corpus,output,check,args.ledger_row,args.study_protocol)
                    completed.append('TP37')
                elif args.card == 'TP36':
                    from tompathy_engine.eval.readers.tp36 import run
                    if not args.ledger_row or not args.study_protocol or not args.primary_job:
                        raise ValueError('TP36 requires its original TP28 export, protocol and ledger identity')
                    run(args.primary_job,args.ed,args.go,args.corpus,output,check,args.ledger_row,args.study_protocol)
                    completed.append('TP36')
                elif args.card == 'TP38':
                    from tompathy_engine.eval.readers.tp38 import run
                    if not all((args.ledger_row,args.study_protocol,args.primary_job)):
                        raise ValueError('TP38 requires G1 and TP28 source bindings and its registered protocol')
                    run(args.ed,args.primary_job,args.prepared,output,check,args.ledger_row,args.study_protocol)
                    completed.append('TP38')
                elif args.card in ('RD1','RD2'):
                    from tompathy_engine.eval.readers.word_panels import run
                    if not all((args.ledger_row,args.study_protocol,args.primary_job,args.reader_job)):
                        raise ValueError('Panel scoring requires its verified source, trained comparator, protocol and ledger identity')
                    run(args.card,args.corpus,args.prepared,args.primary_job,args.reader_job,output,check,
                        args.ledger_row,args.study_protocol,companion=args.coverage_job)
                    completed.append(args.card)
                elif args.card == 'TP30-frozen':
                    from tompathy_engine.eval.readers.tp30 import run
                    if args.ledger_row is None or args.study_protocol is None or args.vector_source is None:
                        raise ValueError('TP30 requires protocol, completed vector source and ledger row')
                    run(args.corpus, args.ed, args.go, args.models, output, check,
                        source_job=args.vector_source, ledger=args.ledger_row, protocol=args.study_protocol)
                    completed.append('TP30-frozen')
                elif args.card == 'TP29':
                    from tompathy_engine.eval.readers.tp29 import run
                    if args.ledger_row is None or args.study_protocol is None:
                        raise ValueError('TP29 requires a frozen protocol and preassigned ledger row')
                    run(args.corpus, args.ed, args.go, args.models, output, check,
                        ledger=args.ledger_row, protocol=args.study_protocol)
                    completed.append('TP29')
                elif args.card == 'TP28':
                    from tompathy_engine.eval.readers.tp28 import run
                    if args.needs_job is None or args.ledger_row is None:
                        raise ValueError('TP28 requires completed C0 and a preassigned ledger row')
                    run(args.needs_job, args.ed, args.go, args.corpus, output, check, ledger=args.ledger_row)
                    completed.append('TP28')
                elif args.card == 'TP23':
                    from tompathy_engine.eval.readers.tp23 import run
                    run(args.rated_data,args.corpus,args.models,output,check,rung=args.rung,seed=args.seed,bundle=args.bundle,
                        fold=args.fold,fold_jobs=args.fold_jobs,preflight_job=args.primary_job,
                        vector_cache=args.vector_cache,vector_source=args.vector_source,preflight_decision=args.preflight_decision)
                    completed.append('TP23 '+args.rung)
                elif args.card == 'TP25':
                    from tompathy_engine.eval.readers.tp25 import run
                    run(args.rated_data,args.corpus,args.go,args.models,args.prepared,output,check,
                        vector_cache=args.vector_cache,vector_source=args.vector_source)
                    completed.append('TP25')
                elif args.card == 'TP24-mixed':
                    from tompathy_engine.eval.readers.tp24_mixed import run
                    if not all((args.primary_job,args.coverage_job,args.reader_job,args.needs_job,
                                args.vector_source,args.ledger_row,args.study_protocol)):
                        raise ValueError('Amended TP24 requires both rosters, C0, need logits, TP30, protocol and ledger row')
                    run(args.corpus,args.primary_job,args.coverage_job,args.reader_job,args.needs_job,
                        args.vector_source,output,check,args.ledger_row,args.study_protocol)
                    completed.append('TP24-mixed')
                elif args.card == 'TP24':
                    from tompathy_engine.eval.readers.tp24 import run
                    run(args.corpus,args.reader_job,args.needs_job,args.models,output,check,
                        vector_cache=args.vector_cache,vector_source=args.vector_source)
                    completed.append('TP24')
                elif args.card == 'TP27':
                    from tompathy_engine.eval.readers.tp27 import run
                    run(args.attention_source,args.primary_job,args.models/'smol135',output,check)
                    completed.append('TP27 diagnostic')
                elif args.card == 'TP12-gated':
                    from tompathy_engine.eval.readers.tp12 import run
                    if args.gate_job is None:
                        raise ValueError('The new counting row requires a qualified gate')
                    run(args.corpus,args.reader_job,output,check,fine_tuned=True,reference=args.counting,gate_job=args.gate_job)
                    completed.append('TP12 gated grid')
                elif args.card == 'TS3-real':
                    from tompathy_engine.eval.readers.trigger_acceptance import run
                    if args.vector_cache is not None and not args.vector_cache.resolve().is_relative_to(root/'.local'):
                        raise ValueError('Runtime vector cache must remain private')
                    run(args.packs,args.source_config,output,check,cache=args.vector_cache)
                    completed.append('TS3 real packets')
                elif args.card == 'TP7':
                    from tompathy_engine.eval.readers.tp7 import run
                    run(args.rated_data, args.primary_job, output, check)
                    completed.append('TP7')
                elif args.card == 'TP26':
                    from tompathy_engine.eval.readers.tp26 import run
                    run(args.rated_data, args.models, output, check, benchmark=args.primary_job,
                        corpus=args.corpus, ed_root=args.ed, go_root=args.go, prepared=args.prepared)
                    completed.append('TP26')
                elif args.card == 'TP10':
                    from tompathy_engine.eval.readers.tp10 import run
                    run(args.corpus, args.models, args.prepared, output, check, args.resume)
                    completed.append('TP10 L0-L2')
                elif args.card in {'TP12','TP12-L3'}:
                    from tompathy_engine.eval.readers.tp12 import run
                    if args.ladder is None:
                        raise ValueError('TP12 requires the completed TP10 ladder')
                    run(args.corpus, args.ladder, output, check,
                        fine_tuned=args.card=='TP12-L3',reference=args.counting)
                    completed.append(args.card)
                elif args.card == 'TP10-L3':
                    from tompathy_engine.eval.readers.finetune import run
                    if args.ladder is None:
                        raise ValueError('L3 requires the completed TP10 L0–L2 ladder')
                    run(args.corpus, args.models, args.prepared, args.ladder, output, check)
                    completed.append('TP10 L3')
                elif args.card == 'TP11':
                    from tompathy_engine.eval.readers.tp11 import run
                    run(args.corpus, args.models, output, check)
                    completed.append('TP11')
                elif args.card == 'TP14':
                    from tompathy_engine.eval.readers.tp14 import run
                    if args.twins is None:
                        raise ValueError('TP14 needs completed TP11 controls')
                    run(args.corpus,args.ed,args.models,args.prepared,args.motive_head,args.twins,output,check)
                    completed.append('TP14')
                elif args.card == 'TP13':
                    from tompathy_engine.eval.readers.tp13 import run
                    if args.reader_job is None:
                        raise ValueError('TP13 requires the completed selected TP10 reader')
                    run(args.corpus,args.ed,args.go,args.reader_job,output,check)
                    completed.append('TP13')
                elif args.card in {'TP15','TP16'}:
                    from tompathy_engine.eval.readers.rated import run
                    if args.rated_data is None:
                        raise ValueError('A verified rated corpus is required')
                    run(args.card,args.rated_data,args.models,output,check,
                        ed_root=args.ed,go_root=args.go,counting=args.counting,reader_job=args.reader_job,resume=args.resume)
                    completed.append(args.card)
                elif args.card == 'TP18':
                    from tompathy_engine.eval.readers.tp18 import run
                    run(args.attention_source,output,check)
                    completed.append('TP18')
                elif args.card == 'TP17':
                    from tompathy_engine.eval.readers.tp17 import run
                    if args.coverage_job is None or args.reader_job is None:
                        raise ValueError('TP17 requires completed TP13 and its exact TP10 reader')
                    run(args.emocause,args.ed,args.coverage_job,args.reader_job,output,check)
                    completed.append('TP17')
                elif args.card == 'TP20':
                    from tompathy_engine.eval.readers.tp20 import run
                    if args.reader_job is None:
                        raise ValueError('TP20 requires the completed TP10 reader')
                    run(args.casino,args.reader_job,output,check)
                    completed.append('TP20')
                elif args.card == 'TP4-controls':
                    from tompathy_engine.eval.readers.goal_controls import run
                    run(args.prepared,args.goal_baseline,output,check)
                    completed.append('TP4-controls')
                elif args.card == 'TP18-probe':
                    from tompathy_engine.eval.readers.tp18_probe import run
                    if args.primary_job is None:
                        raise ValueError('Conditional probe requires its completed TP18 primary')
                    run(args.primary_job,args.attention_source,args.smol,output,check)
                    completed.append(args.card)
                elif args.card == 'TP19':
                    from tompathy_engine.eval.readers.tp19 import run
                    if args.reader_job is None:
                        raise ValueError('TP19 requires the completed TP10 reader')
                    run(args.ledger,args.reader_job,output,check,motive_job=args.motive_job,
                        models=args.models,motive_head=args.motive_head,source_config=args.source_config,resume=args.resume)
                    completed.append(args.card)
                elif args.card in {'TP22','TP22-gated'}:
                    from tompathy_engine.eval.readers.tp22 import run
                    if args.reader_job is None:
                        raise ValueError('TP22 requires the completed TP10 reader and counting policy')
                    run(args.blogs,args.reader_job,args.counting,args.models,output,check,
                        gate_job=args.gate_job if args.card == 'TP22-gated' else None)
                    completed.append(args.card)
                elif args.card == 'TP1c':
                    from tompathy_engine.eval.readers.tp1c import run
                    run(args.models/'smol135',args.smol,args.converter,args.speed_texts,args.intake,output,check)
                    completed.append(args.card)
                for name, script in scripts.items():
                    check()
                    sys.argv = [str(script), str(args.corpus.resolve()), str(output)]
                    save_json(output/'phase.json', {'phase': name, 'at': datetime.now(UTC).isoformat()})
                    with (output/(name+'.txt')).open('w', encoding='utf8') as stream, redirect_stdout(stream):
                        sys.settrace(trace)
                        try:
                            runpy.run_path(str(script), run_name='__main__')
                        finally:
                            sys.settrace(None)
                    completed.append(name)
                    save_json(output/'progress.json', {'completed': completed})
        save_json(output/'complete.json', {'at': datetime.now(UTC).isoformat(), 'completed': completed})
    except Exception as exc:
        save_json(output/'failed.json', {'at': datetime.now(UTC).isoformat(),
            'reason': str(exc), 'type': type(exc).__name__, 'completed': completed})
        raise


if __name__ == '__main__':
    main()
