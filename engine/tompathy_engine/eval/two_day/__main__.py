"""Explicit private pilot entry point. Use the counted-job launcher on this host."""
import argparse
from pathlib import Path

from ...preview.readers import LocalReader
from ..back_half.reporting import save_json
from ..back_half.resources import benchmark_priority, guard
from .exports import read


def main(argv=None, *, check=guard):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('task', choices=('edit-features', 'edits', 'human-edits', 'human-features', 'goals', 'goal-baseline', 'robustness', 'choice', 'choice-goals', 'weightonly', 'weightonly-binding', 'first-paint'))
    parser.add_argument('--prepared', type=Path, default=Path('.local/bench/two-day-prepared'))
    parser.add_argument('--readers', type=Path, default=Path('.local/preview-readers'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--dataset', type=Path)
    parser.add_argument('--auxiliary', type=Path)
    parser.add_argument('--omit-paraphrase', action='store_true')
    parser.add_argument('--url', help='Dedicated loopback service owned by the invoking wrapper')
    parser.add_argument('--model', choices=('qwen', 'smol'), default='qwen')
    parser.add_argument('--gguf', type=Path)
    parser.add_argument('--texts', type=Path)
    parser.add_argument('--e1-output', type=Path)
    parser.add_argument('--feature-output', type=Path)
    parser.add_argument('--attention-output', type=Path)
    parser.add_argument('--weightonly-receipt', type=Path)
    parser.add_argument('--intake', type=Path, default=Path('.local/bench/two-day-ex1-intake'))
    args = parser.parse_args(argv)
    if not args.output.resolve().is_relative_to(Path('.local/bench').resolve()):
        parser.error('Individual observations must remain under .local/bench')
    benchmark_priority(2)
    check()
    from .pilots import edit_run, goal_run, lexical_baseline, robustness_run
    if args.task == 'edit-features':
        from .edit_features import run
        return run(args.prepared, args.output, check)
    if args.task == 'human-features':
        from .edit_features import human_baseline
        result = human_baseline(args.prepared)
        save_json(args.output/'receipt.json', result)
        return result
    if args.task in {'edits', 'human-edits', 'goals', 'choice-goals'} and not args.url:
        parser.error('This pilot requires its own dedicated 9B service')
    if args.task in {'robustness', 'choice', 'choice-goals'} and args.dataset is None:
        parser.error('Explicit dataset required')
    if args.task in {'edits', 'human-edits'}:
        return edit_run(args.prepared, args.output, args.url, check, human=args.task == 'human-edits', feature_output=args.feature_output)
    if args.task == 'goal-baseline':
        from ...admission import implementation_hash
        from ...ledger.ids import digest
        from .pilots import lexical_summary
        tasks = read(args.prepared/'goals.json')
        result = lexical_baseline(tasks)
        save_json(args.output/'tfidf.json', result)
        report = {'status': 'baseline complete; goal readers pending', 'tfidfBaseline': lexical_summary(result),
                  'dataPin': digest(tasks), 'codePin': implementation_hash(), 'productionAdmission': False}
        save_json(args.output/'receipt.json', report)
        return report
    if args.task == 'goals':
        return goal_run(args.prepared, args.readers, args.output, args.url, check)
    if args.task == 'robustness':
        return robustness_run(args.dataset, args.readers, args.output, check, model=args.model,
                              auxiliary=args.auxiliary, omit_paraphrase=args.omit_paraphrase)
    if args.task == 'choice':
        from .choice import choice_run
        reader = LocalReader(args.readers/args.model, args.output.parent/'choice-token-cache', threads=2, precision='float32')
        return choice_run(args.dataset, args.output, reader, check)
    if args.task == 'choice-goals':
        from ...admission import implementation_hash
        from ...ledger.ids import digest
        from ...preview.fixed_backend import FixedQwen
        from ...transcribe.cache import Cache
        from ..back_half.reporting import bind_run
        from ..back_half.state import PilotDeadline
        from .choice import choice_goals, completed_e1, load_choice
        if not args.e1_output:
            parser.error('E2 requires completed paired E1 observations')
        rows, pin = load_choice(args.dataset)
        completed = completed_e1(args.e1_output, rows, pin)
        identity = {'task': 'TP7-E2', 'dataPin': pin, 'codePin': implementation_hash(), 'pairedE1Pin': digest(completed)}
        bind_run(args.output, identity)
        deadline = PilotDeadline(args.output/'deadline.json')
        def bounded():
            check(); deadline.check()
        backend = None
        report = {'status': 'running', 'identity': identity, 'productionAdmission': False, 'completedQuestions': 0}
        try:
            bounded(); guard(large_model=True)
            backend = FixedQwen(args.url, timeout=600, before_load=lambda: guard(large_model=True))
            report['readerPin'] = digest([backend.model_id, backend.settings, implementation_hash()])
            def progress(value):
                report['completedQuestions'] = len(value)
                save_json(args.output/'observations.json', value)
            result = choice_goals(rows, completed, backend, Cache(args.output/'goals.sqlite'), bounded,
                                  progress)
            report.update(result, status='complete')
            return report
        except Exception as exc:
            report.update(status='stopped', reason=f'{type(exc).__name__}: {exc}')
            raise
        finally:
            try:
                if backend:
                    backend.close(recover=True)
            except Exception:
                report.update(status='cleanup-failed', cleanup='failed')
                raise
            finally:
                save_json(args.output/'receipt.json', report)
    if args.task == 'weightonly':
        from .weightonly import run
        if not args.gguf or not args.texts:
            parser.error('W1 requires converted local GGUF and the three frozen texts')
        return run(args.readers/'qwen', args.gguf, read(args.texts), args.output/'receipt.json', check)
    if args.task == 'weightonly-binding':
        from ...admission import implementation_hash
        from ...ledger.ids import digest
        from .attention import score_resumable
        from .weightonly import WeightOnlyReader, finish_binding
        if not args.gguf or not args.weightonly_receipt or not args.attention_output:
            parser.error('Binding requires converted weights, completed gates a-d, and the exact reference run')
        previous = read(args.weightonly_receipt)
        if previous['status'] != 'awaiting gate e: exact-cohort TP2 binding' or previous['codePin'] != implementation_hash():
            raise ValueError('Weight-only binding cannot bypass changed code or an earlier failed gate')
        reader = WeightOnlyReader(args.readers/'qwen', args.gguf, threads=2, cache=args.output.parent/'weightonly-raw-cache')
        try:
            if digest(reader.identity) != previous['readerPin']:
                raise ValueError('Weight-only binding reader pin differs')
            data_pin = digest(read(args.intake/'intake.json'))
            if read(args.attention_output/'attention-window.json')['dataPin'] != data_pin:
                raise ValueError('Weight-only binding source intake differs')
            tables, _ = score_resumable(read(args.intake/'sessions.json'), reader, args.output, data_pin, {}, check)
            return finish_binding(args.weightonly_receipt, read(args.attention_output/'window/tables.json'), tables,
                                  reader_identity=reader.identity, data_pin=data_pin)
        finally:
            reader.close()
    if args.task == 'first-paint':
        from .weightonly import first_paint
        if not args.texts or not args.attention_output:
            parser.error('First paint requires frozen texts and a measured reader ladder')
        return first_paint(args.readers, read(args.texts), args.output, check, read(args.attention_output/'reader-ladder.json'))


if __name__ == '__main__':
    main()
