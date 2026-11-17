"""Within-writer log-pause remainder. Diagnostic, never an independent stop key."""
from collections import Counter, defaultdict

import numpy as np

from ..preview.surface import WORD


def add_remainder(tables, check=lambda: None):
    """OLS with intercept on each writer's valid timing rows, no label tuning.

    The supplied stop outcome derives from this same pause. Residuals are not
    prospective forecasts, even if a downstream classifier holds writers out.
    Missing timing rows remain missing rather than becoming zero hesitation.
    """
    writers = defaultdict(list)
    frequencies = defaultdict(Counter)
    for session in tables:
        frequencies[session['writer']].update(m.group().casefold() for m in WORD.finditer(session['text']))
        for word in session['words']:
            if word['source'] == 'writer' and word.get('logPause') is not None:
                writers[session['writer']].append(word)
    summaries = []
    for writer, rows in writers.items():
        check()
        x = np.asarray([[len(w['text']), np.log1p(frequencies[writer][w['text'].casefold()]),
                         w['sentenceStart'], w['scores']['after_punctuation'], w['scores']['smol135_nats']]
                        for w in rows], float)
        y = np.asarray([w['logPause'] for w in rows], float)
        if not np.isfinite(x).all() or not np.isfinite(y).all():
            raise ValueError('Pause regression needs finite saved timing and features')
        z = np.column_stack([np.ones(len(x)), (x-x.mean(0))/(x.std(0)+1e-9)])
        coefficients, _, rank, _ = np.linalg.lstsq(z, y, rcond=None)
        residual = y-z@coefficients
        for row, value in zip(rows, residual):
            row['scores']['pause_remainder'] = float(value)
        summaries.append({'rows': len(rows), 'rank': int(rank), 'residual_sd': float(residual.std())})
    return {'writers': len(summaries), 'rows': sum(r['rows'] for r in summaries),
            'rank_deficient_writers': sum(r['rank'] < 6 for r in summaries),
            'diagnostic_only': True, 'stop_label_uses_same_pause': True}
