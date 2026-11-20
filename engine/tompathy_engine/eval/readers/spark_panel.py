"""Fixed SP1 cross-reader comparison on common first-pass rows; no inference."""
import numpy as np
from scipy.stats import spearmanr


def compare_first_passes(reader_a, reader_b, truth, baseline, qualified):
    if len(reader_a) != 300 or len(reader_b) != 300 or set(qualified) != {'a', 'b'}:
        raise ValueError('Two complete fixed panels and their qualification states required')
    if any(type(v) is not bool for v in qualified.values()):
        raise ValueError('Qualification states must be explicit Booleans')
    truth, baseline = np.asarray(truth, float), np.asarray(baseline, float)
    if (truth.shape != (300, 8) or baseline.shape != truth.shape or
            not np.isfinite(truth).all() or not np.isfinite(baseline).all()):
        raise ValueError('The exact finite writer and saved-comparator tables are required')
    def validate(rows):
        for row in rows:
            if row is not None and (not isinstance(row, list) or len(row) != 8 or
                                    any(type(v) is not int or not 1 <= v <= 5 for v in row)):
                raise ValueError('Only parsed original integer ratings or explicit invalids are allowed')
        return np.array([row is not None for row in rows])
    common = validate(reader_a) & validate(reader_b)
    def score(rows):
        values = np.asarray([row for row, keep in zip(rows, common) if keep], float)
        reference = truth[common]
        scores = []
        for feature in range(8):
            if (len(values) < 3 or len(np.unique(values[:, feature])) < 2 or
                    len(np.unique(reference[:, feature])) < 2):
                scores.append(None)
            else:
                scores.append(float(spearmanr(values[:, feature], reference[:, feature]).statistic))
        return {'featureSpearman': scores,
                'meanSpearman': float(np.mean(scores)) if all(v is not None for v in scores) else None}
    scores = {'a': score(reader_a), 'b': score(reader_b)}
    control = score(baseline)
    selected = None
    if all(row['meanSpearman'] is not None for row in scores.values()):
        # Fixed A tie-break; a failed selected reader is not replaced post hoc.
        selected = max(('a', 'b'), key=lambda role: scores[role]['meanSpearman'])
    return {'n': 300, 'commonValid': int(common.sum()), 'scores': scores,
            'baselineSameRows': control, 'selectedRole': selected,
            'selectedReaderQualified': qualified[selected] if selected is not None else False,
            'standaloneQualification': dict(qualified), 'productionAdmission': False,
            'scope': 'Common first-pass rows only; completed standalone gates remain unchanged. No model IDs or target tables pooled.'}
