"""W1 local GGUF scorer and ordered parity gates. Never retries a failed gate."""
import gc
import importlib.metadata
from pathlib import Path
from time import monotonic

import numpy as np
from scipy.special import logsumexp

from ...admission import implementation_hash
from ...ledger.ids import digest
from ...preview.kv_reader import segments
from ...preview.readers import LocalReader
from ...preview.surface import WORD
from ..back_half.attention import binding_parity
from ..back_half.reporting import save_json
from ..back_half.speed import comparison
from .exports import read, sha


def vocabulary_gate(tokenizer, runtime, model_vocabulary_size, *, allow_unused_padding=False):
    reference = tokenizer.get_vocab()
    actual = {runtime._model.token_get_text(i): i for i in range(runtime.n_vocab())}
    mismatches = sum(actual.get(token) != ident for token, ident in reference.items())
    extra = len(set(actual)-set(reference))
    assigned_ids = set(reference.values())
    unused = [i for i in range(runtime.n_vocab()) if i not in assigned_ids]
    # Owner-authorized November 13 clarification. Token attribute 2 is the
    # pinned llama.cpp LLAMA_TOKEN_ATTR_UNUSED bit; no other attributes qualify.
    padding_valid = (runtime.n_vocab() == model_vocabulary_size and len(actual) == runtime.n_vocab()
                     and all(runtime._model.token_get_text(i) == f'[PAD{i}]'
                             and runtime._model.token_get_attr(i) == 2 for i in unused))
    equivalent = allow_unused_padding and mismatches == 0 and padding_valid
    return {'passed': (actual == reference and runtime.n_vocab() == model_vocabulary_size) or equivalent, 'assignedTokenMismatches': mismatches,
            'engineTokenizerEntries': len(reference), 'runtimeEntries': runtime.n_vocab(),
            'modelOutputRows': model_vocabulary_size, 'extraRuntimeEntries': extra,
            'unusedPaddingEquivalence': allow_unused_padding, 'verifiedUnusedPaddingRows': len(unused) if padding_valid else 0,
            'definition': 'Assigned token strings/IDs identical; optional owner-authorized unused padding must match original output size, exact PAD IDs and UNUSED-only attributes.'}


class WeightOnlyReader:
    def __init__(self, directory, gguf, *, threads=2, cache=None):
        import llama_cpp
        from transformers import AutoTokenizer
        self.directory, self.cache = Path(directory), Path(cache) if cache else None
        manifest = read(self.directory/'manifest.json')
        self.manifest, self.device, self.scoring = manifest, 'cpu', 'kv'
        actual = {p.name for p in self.directory.iterdir() if p.is_file() and p.name != 'manifest.json'}
        if threads not in (1, 2) or manifest['model'] != 'Qwen/Qwen2.5-0.5B':
            raise ValueError('W1 requires the pinned base reader and one or two CPU threads')
        if actual != set(manifest['files']) or not {'config.json', 'tokenizer.json', 'model.safetensors'} <= actual:
            raise ValueError('Original manifest must pin every local model/tokenizer file')
        if any(sha(self.directory/name) != expected for name, expected in manifest['files'].items()):
            raise ValueError('Original model pin differs')
        self.tokenizer = AutoTokenizer.from_pretrained(self.directory, local_files_only=True, trust_remote_code=False)
        self.identity = {'id': manifest['model'], 'revision': manifest['revision'], 'sha256': digest(manifest),
            'gguf': sha(gguf), 'runtime': importlib.metadata.version('llama-cpp-python'),
            'backend': f'llama.cpp Q8_0 CPU {threads} threads; KV2048/rebuild1024; engine token IDs'}
        start = monotonic()
        self.model = llama_cpp.Llama(model_path=str(gguf), n_ctx=2048, n_batch=1024, n_ubatch=512,
            n_threads=threads, n_threads_batch=threads, n_gpu_layers=0, logits_all=True, verbose=False,
            flash_attn=False, seed=0, offload_kqv=False)
        self.metrics = {'loadMs': (monotonic()-start)*1000, 'scoreMs': 0., 'cacheHits': 0, 'forwardCalls': 0, 'inputTokens': 0}
        self.entropy = False
        if self.cache:
            self.cache.mkdir(parents=True, exist_ok=True)

    def encode(self, text):
        return self.tokenizer(text, add_special_tokens=False, return_offsets_mapping=True)

    def score(self, text, context='', check=lambda: None):
        result = []
        for result, _ in self.score_chunks(text, context, check):
            pass
        return result

    def score_chunks(self, text, context='', check=lambda: None):
        key = digest([self.identity, text, context, 'w1-kv-v1'])
        path = self.cache/f'{key}.json' if self.cache else None
        if path and path.exists():
            saved = read(path)
            if saved['key'] != key or saved['sha256'] != digest(saved['tokens']):
                raise ValueError('Weight-only cache integrity failure')
            self.metrics['cacheHits'] += 1
            yield saved['tokens'], True
            return
        encoded = self.encode(text)
        target, offsets = encoded['input_ids'], encoded['offset_mapping']
        prefix = (context if isinstance(context, list) else self.encode(context)['input_ids'])[-1536:]
        bos = self.tokenizer.bos_token_id
        if bos is None:
            bos = self.tokenizer.eos_token_id
        if bos is None:
            raise ValueError('Engine beginning token missing')
        start_time, out = monotonic(), []
        for start, previous, segment in segments(target, prefix, bos):
            check()
            self.model.reset()
            self.model.eval(previous)
            self.metrics['forwardCalls'] += 1
            self.metrics['inputTokens'] += len(previous)
            for local in range(0, len(segment), 512):
                check()
                chunk = segment[local:local+512]
                before = self.model.n_tokens
                self.model.eval(chunk)
                self.metrics['forwardCalls'] += 1
                self.metrics['inputTokens'] += len(chunk)
                logits = self.model.scores[before-1:before+len(chunk)-1]
                losses = logsumexp(logits, axis=-1)-logits[np.arange(len(chunk)), np.array(chunk)]
                for i, loss in enumerate(losses, start+local):
                    a, b = offsets[i]
                    if b > a:
                        out.append({'start': a, 'end': b, 'nats': float(loss)})
                check()
                yield list(out), start+local+len(chunk) == len(target)
        self.metrics['scoreMs'] += (monotonic()-start_time)*1000
        if path:
            save_json(path, {'key': key, 'sha256': digest(out), 'tokens': out})

    def prefix_probe(self, text):
        ids = self.encode(text)['input_ids'][:1024]
        if len(ids) != 1024:
            raise ValueError('Prefix gate requires 1024 tokens')
        values = []
        for count in (512, 1024):
            self.model.reset()
            self.model.eval(ids[:count])
            logits = self.model.scores[:511]
            values.append(logsumexp(logits, axis=-1)-logits[np.arange(511), np.array(ids[1:512])])
        delta = abs(values[0]-values[1])
        return {'maxAbsoluteTokenNats': float(delta.max()), 'passed': bool(np.all(delta < .001))}

    def close(self):
        self.model.close()


def ready(receipt, *, reader_pin, data_pin):
    return receipt.get('status') == 'complete' and receipt.get('readerPin') == reader_pin and receipt.get('dataPin') == data_pin and all(
        receipt.get('gates', {}).get(name, {}).get('passed') is True for name in 'abcde')


def finish_binding(path, reference_tables, candidate_tables, *, reader_identity, data_pin):
    report = read(path)
    if report.get('status') != 'awaiting gate e: exact-cohort TP2 binding' or not all(report['gates'][k]['passed'] for k in 'abcd'):
        raise ValueError('Cannot bypass or resume a failed weight-only gate')
    if digest(reader_identity) != report['readerPin'] or implementation_hash() != report['codePin']:
        raise ValueError('Weight-only reader/code changed before binding parity')
    result = binding_parity(reference_tables, candidate_tables)
    report['gates']['e'] = {**result, 'passed': result['passes']}
    report['dataPin'] = data_pin
    report['status'] = 'complete' if result['passes'] else 'stopped at gate e'
    save_json(path, report)
    return report


def load_admitted_route(directory, gguf, receipt_path, *, threads, cache=None):
    report = read(receipt_path)
    if report.get('codePin') != implementation_hash() or not report.get('dataPin') or report.get('ggufPin') != sha(gguf):
        raise ValueError('Weight-only route requires current code, data and converted-weight pins')
    if not ready(report, reader_pin=report.get('readerPin'), data_pin=report['dataPin']):
        raise ValueError('Weight-only route requires all five parity gates; no failed or pending gate may be bypassed')
    reader = WeightOnlyReader(directory, gguf, threads=threads, cache=cache)
    if digest(reader.identity) != report['readerPin']:
        reader.close()
        raise ValueError('Weight-only runtime, thread setting or tokenizer differs from its passed receipt')
    return reader


def first_paint(readers, texts, output, check, ladder):
    report = {'status': 'running', 'textPin': digest(texts), 'codePin': implementation_hash(), 'measurements': [],
              'readerLadderPin': digest(ladder), 'defaultChanged': False}
    models = ('qwen', 'smol') if ladder.get('status') == 'complete' and ladder.get('candidateFirstPaint') is True else ('qwen',)
    for model in models:
        check()
        reader = LocalReader(Path(readers)/model, threads=2, precision='float32', scoring='kv')
        try:
            for name, text in texts.items():
                source_words = list(WORD.finditer(text))
                if not source_words:
                    raise ValueError('Empty first-paint text')
                boundary = source_words[min(600, len(source_words))-1].end()
                started, first = monotonic(), None
                for tokens, _ in reader.score_chunks(text, check=check):
                    if first is None and tokens and tokens[-1]['end'] >= boundary:
                        first = monotonic()-started
                report['measurements'].append({'model': model, 'reader': reader.identity, 'text': name,
                    'loadSeconds': reader.metrics['loadMs']/1000, 'first600WordsSeconds': first,
                    'totalSeconds': monotonic()-started, 'words': len(source_words), 'threads': 2})
                save_json(Path(output)/'receipt.json', report)
        finally:
            del reader
            gc.collect()
    report['status'] = 'complete'
    save_json(Path(output)/'receipt.json', report)
    return report


def run(directory, gguf, texts, output, check, *, reference_tables=None, candidate_tables=None, data_pin=None):
    output = Path(output)
    if output.exists():
        raise ValueError('Preserve earlier gate receipt; a failed research route cannot be rerun')
    report = {'schema': 'tompathy.speed-weightonly.v1', 'route': 'W1', 'status': 'running', 'gates': {},
              'defaultChanged': False, 'productionEnabled': False, 'codePin': implementation_hash(),
              'ggufPin': sha(gguf), 'textsPin': digest(texts), 'measurements': []}
    reader = None
    def gate(name, value):
        report['gates'][name] = value
        if not value['passed']:
            report['status'] = f'stopped at gate {name}'
        save_json(output, report)
        return value['passed']
    try:
        check()
        reader = WeightOnlyReader(directory, gguf, threads=2)
        report['readerPin'] = digest(reader.identity)
        if not gate('a', vocabulary_gate(reader.tokenizer, reader.model, read(Path(directory)/'config.json')['vocab_size'], allow_unused_padding=True)):
            return report
        candidate = {name: reader.score(text, check=check) for name, text in texts.items()}
        reader.close(); reader = None
        check()
        reference = LocalReader(directory, threads=2, precision='float32')
        try:
            rows = {name: comparison(text, reference.score(text, check=check), candidate[name]) for name, text in texts.items()}
        finally:
            del reference
            gc.collect()
        if not gate('b', {'passed': all(r['spearman'] >= .98 and r['medianAbsoluteNats'] <= .05 for r in rows.values()), 'texts': rows}):
            return report
        reader = WeightOnlyReader(directory, gguf, threads=2)
        if not gate('c', reader.prefix_probe(next(iter(texts.values())))):
            return report
        reader.close(); reader = None
        for threads in (1, 2):
            check()
            reader = WeightOnlyReader(directory, gguf, threads=threads)
            for name, text in texts.items():
                boundary = list(WORD.finditer(text))[min(600, len(list(WORD.finditer(text))))-1].end()
                started, first = monotonic(), None
                for tokens, _ in reader.score_chunks(text, check=check):
                    if first is None and tokens and tokens[-1]['end'] >= boundary:
                        first = monotonic()-started
                elapsed = monotonic()-started
                report['measurements'].append({'text': name, 'threads': threads, 'loadSeconds': reader.metrics['loadMs']/1000,
                    'first600WordsSeconds': first, 'totalSeconds': elapsed, 'secondsPer3000Words': elapsed*3000/len(list(WORD.finditer(text)))})
                save_json(output, report)
            reader.close(); reader = None
        gate('d', {'passed': True, 'targetSecondsPer3000Words': 15, 'definition': 'recorded timing; target is not an accuracy waiver'})
        if reference_tables is None or candidate_tables is None:
            report['status'] = 'awaiting gate e: exact-cohort TP2 binding'
        else:
            parity = binding_parity(reference_tables, candidate_tables)
            gate('e', {**parity, 'passed': parity['passes']})
            report['dataPin'] = data_pin
            if parity['passes']:
                report['status'] = 'complete'
        return report
    except Exception as exc:
        report.update(status='engineering failure', reason=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        if reader:
            reader.close()
        save_json(output, report)
