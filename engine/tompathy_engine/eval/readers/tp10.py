"""Frozen channel ladder L0–L2 and human/model answer-key reproduction."""
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import accuracy_score, f1_score

from ...packs.registry import sha256
from ..back_half.reporting import save_json
from .encoders import embeddings, load_encoder
from .envent import RATINGS, READABLE, human_rows, load
from .metrics import channel_gates, classification, confusion


def harness(corpus, directory):
    result = {}
    for name, (y, prediction) in human_rows(corpus).items():
        result[name] = {'accuracy': float(accuracy_score(y, prediction)),
                        'macro_f1': float(f1_score(y, prediction, average='macro'))}
    test = corpus.reports.iloc[corpus.test].set_index('text_id')
    index = dict(zip(corpus.labels, range(len(corpus.labels))))
    scores = []
    for path in sorted(Path(directory).glob('predictions/TEmodel_classifier_*.tsv')):
        pred = pd.read_csv(path, sep='\t').set_index('text_id').loc[test.index].predicted_emotion.map(index)
        scores.append([accuracy_score(test.y, pred), f1_score(test.y, pred, average='macro')])
    if len(scores) != 5:
        raise ValueError('Expected five released prediction files')
    result['authors_mean'] = dict(zip(('accuracy', 'macro_f1'), np.mean(scores, axis=0).tolist()))
    expected = {'single': (.504, .492, .002), 'majority': (.581, .565, .01),
                'authors_mean': (.605, .594, .002)}
    result['passed'] = all(abs(result[n]['accuracy']-a) <= tolerance and
        abs(result[n]['macro_f1']-f) <= tolerance for n, (a,f,tolerance) in expected.items())
    return result


def neutral_texts(prepared):
    battery = json.loads(Path('engine/validation/q10-empty-v2.items.json').read_text(encoding='utf8'))
    themes = [r['text'] for r in battery if r['expected'] == []]
    # Require the prepared neutral-input adapter receipt; a missing set is not a pass.
    path = Path(prepared)/'readers-neutral-before.json'
    revisions = json.loads(path.read_text(encoding='utf8')) if path.exists() else []
    if revisions:
        intake = json.loads((path.parent/'neutral-intake.json').read_text(encoding='utf8'))
        if intake['outputPin'] != sha256(path) or intake['n'] != len(revisions):
            raise ValueError('Neutral revision intake differs')
    if any(r.get('source') not in {'arxiv', 'wikipedia'} or not r.get('before') for r in revisions):
        raise ValueError('Neutral revision input provenance missing')
    return themes, [r['before'] for r in revisions][:2000], intake if revisions else {}


def run(directory, models, prepared, output, check, resume=None):
    output = Path(output)
    corpus = load(directory)
    report = {'card': 'TP10', 'status': 'running', 'scope': corpus.summary(),
              'harness': harness(corpus, directory), 'rows': {}, 'productionAdmission': False}
    save_json(output/'receipt.json', report)
    if not report['harness']['passed']:
        raise RuntimeError('Preflight reproduction differs from its registered tolerance')
    frame, train, dev, test = corpus.reports, corpus.train, corpus.dev, corpus.test
    y = frame.y.to_numpy()
    k = len(corpus.labels)
    themes, revisions, neutral_intake = neutral_texts(prepared)
    report['neutralInputs'] = {'themeFreeSourcePin': sha256('engine/validation/q10-empty-v2.items.json'),
        'revisionIntakePin': sha256(Path(prepared)/'neutral-intake.json') if revisions else None}
    if resume:
        resume = Path(resume)
        verified = json.loads((resume/'exit-verification.json').read_text(encoding='utf8'))
        if not all(verified.get(key) for key in
                   ('nativeExited', 'releaseMatches', 'sharedLeaseAbsent', 'localLeaseAbsent')):
            raise ValueError('Previous scorer exit and exact releases must be verified')
        previous = json.loads((resume/'receipt.json').read_text(encoding='utf8'))
        if previous['scope'] != report['scope'] or previous['neutralInputs'] != report['neutralInputs']:
            raise ValueError('Continuation input/split identity differs')
        if previous['status'] != 'running' or not (resume/'failed.json').exists():
            raise ValueError('Only an unfinished engineering-failed ladder may continue')
        # No reinterpretation of completed rows: all numerical paths must match.
        for name in ('envent.py', 'metrics.py', 'encoders.py'):
            prior = resume/'code/tompathy_engine/eval/readers'/name
            if sha256(prior) != sha256(Path(__file__).with_name(name)):
                raise ValueError('Completed numerical path changed')
        retained = {}
        for name, row in previous['rows'].items():
            if name not in {'constant', 'bow', 'potion', 'minilm'}:
                raise ValueError('Unknown retained row')
            if row.get('encoder'):
                intake = json.loads((Path(models)/name/'intake.json').read_text(encoding='utf8'))
                if row['encoder']['files'] != intake['files']:
                    raise ValueError('Retained reader changed')
            for source in resume.glob(name+'-*.npz'):
                shutil.copyfile(source, output/source.name)
                retained[source.name] = sha256(source)
            report['rows'][name] = row
        report['continuation'] = {'sourceReceiptPin': sha256(resume/'receipt.json'),
            'previousFailurePin': sha256(resume/'failed.json'), 'retained': retained,
            'reason': 'Missing Pillow dependency before MiniLM loading; completed rows unchanged'}
    readable = [RATINGS.index(r) for r in READABLE]
    target = frame[RATINGS].to_numpy(float)
    baseline = np.tile(target[train].mean(axis=0), (len(test),1))
    v = corpus.judgments
    single_key = frame.set_index('text_id').loc[v.text_id, RATINGS].to_numpy(float)
    rmse = lambda a,b: float(np.sqrt(np.mean((a-b)**2)))
    feature_floor = {'constant': rmse(baseline[:,readable], target[test][:,readable]),
        'one_reader': rmse(v[RATINGS].to_numpy(float)[:,readable], single_key[:,readable])}
    save_json(output/'split.json', {'train': frame.iloc[train].text_id.tolist(),
        'development': frame.iloc[dev].text_id.tolist(), 'test': frame.iloc[test].text_id.tolist()})
    for name in ['constant', 'bow', 'potion', 'minilm']:
        if name in report['rows']:
            continue
        check()
        save_json(output/'phase.json', {'phase': name})
        identity, timing, feature = None, None, None
        if name == 'constant':
            label = np.bincount(y[train], minlength=k).argmax()
            predict = lambda texts, label=label: np.tile(np.eye(k)[label], (len(texts), 1))
            probabilities = predict(frame.iloc[test].hidden_emo_text)
            dev_probabilities = predict(frame.iloc[dev].hidden_emo_text)
        else:
            if name == 'bow':
                vectorizer = TfidfVectorizer(ngram_range=(1,2), min_df=2, sublinear_tf=True)
                vectorizer.fit(frame.iloc[train].hidden_emo_text)
                x = vectorizer.transform(frame.hidden_emo_text)
                encode = vectorizer.transform
            else:
                x, identity, timing = embeddings(frame.hidden_emo_text, Path(models)/name,
                                                name, output/'embeddings'/name, check)
                encode, _ = load_encoder(Path(models)/name, name)
            check()
            model = LogisticRegression(C=10, max_iter=2000, random_state=20261114).fit(x[train], y[train])
            if list(model.classes_) != list(range(k)):
                raise ValueError('Missing training label')
            predict = lambda texts, model=model, encode=encode: model.predict_proba(encode(list(texts)))
            probabilities, dev_probabilities = model.predict_proba(x[test]), model.predict_proba(x[dev])
            reg = Ridge(alpha=3).fit(x[train], target[train])
            rated = reg.predict(x[test])
            feature = {'all21_rmse': rmse(rated, target[test]),
                'readable8_rmse': rmse(rated[:,readable], target[test][:,readable]),
                'floor': feature_floor, 'readable': READABLE}
            feature['passed'] = all(feature['readable8_rmse'] < v for v in feature_floor.values())
            np.savez(output/(name+'-head.npz'), weights=model.coef_, bias=model.intercept_,
                     ratings_weights=reg.coef_, ratings_bias=reg.intercept_)
        row = classification(y[test], probabilities, frame.iloc[test].prolific_id, corpus.labels)
        row['development_macro_f1'] = float(f1_score(y[dev], dev_probabilities.argmax(axis=1), average='macro'))
        row['features'], row['timing'], row['encoder'] = feature, timing, identity
        neutral = corpus.labels.index('no-emotion')
        checks = {'theme_free_n': len(themes), 'theme_free_silent': 0,
                  'revision_n': len(revisions), 'revision_silent_rate': None,
                  'revision_coverage_complete': neutral_intake.get('coverageComplete', False),
                  'revision_exclusions': neutral_intake.get('excluded', {})}
        theme_probabilities = predict(themes)
        checks['theme_free_silent'] = int((theme_probabilities.argmax(axis=1) == neutral).sum())
        revision_probabilities = []
        if revisions:
            silent = 0
            for i in range(0, len(revisions), 64):
                check()
                batch = predict(revisions[i:i+64])
                revision_probabilities.extend(batch)
                silent += int((batch.argmax(axis=1) == neutral).sum())
            checks['revision_silent_rate'] = silent/len(revisions)
        row['nothing_here'] = checks
        row['development_error_counts'] = confusion(y[dev], dev_probabilities.argmax(axis=1), k).tolist()
        np.savez(output/(name+'-predictions.npz'), test_probabilities=probabilities,
                 development_probabilities=dev_probabilities, y=y[test], writers=frame.iloc[test].prolific_id.to_numpy(str),
                 theme_probabilities=theme_probabilities, revision_probabilities=np.asarray(revision_probabilities))
        report['rows'][name] = row
        save_json(output/'receipt.json', report)
    for name, row in report['rows'].items():
        row['gates'] = channel_gates(row, report['rows']['bow'], row['nothing_here'])
    report['selected_for_L3'] = max(['potion', 'minilm'], key=lambda n: report['rows'][n]['development_macro_f1'])
    report['selection_basis'] = 'Development macro-F1, before any L3 training; test scores do not choose encoder'
    report['status'] = 'L0-L2 complete; L3 and final pack gates pending'
    save_json(output/'receipt.json', report)
    return report
