"""Frozen TP23 transfer protocol, matching the supplied BOW preflight."""
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, roc_auc_score
from sklearn.model_selection import GroupKFold

from .envent import RATINGS

PAIRS = ('pride-joy', 'guilt-shame', 'fear-sadness', 'anger-disgust', 'trust-joy')


def fit_scaled(x, y, train, test, check):
    check()
    mean, sd = x[train].mean(0), x[train].std(0)+1e-9
    model = LogisticRegression(C=1, max_iter=3000).fit((x[train]-mean)/sd, y[train])
    if np.any(model.n_iter_ >= model.max_iter):
        raise RuntimeError('Transfer optimizer did not converge')
    return model, (x[test]-mean)/sd


def transfer(frame, needs, check, *, words=False):
    ratings = frame[RATINGS].to_numpy(float)
    groups = frame.prolific_id.to_numpy()
    labels = frame.emotion.to_numpy()
    twins = {}
    for pair in PAIRS:
        a, b = pair.split('-')
        ids = np.flatnonzero(np.isin(labels, [a, b]))
        y = (labels[ids] == a).astype(int)
        matrices = {'ratings': ratings[ids], 'needs': needs[ids], 'ratings+needs': np.column_stack([ratings[ids], needs[ids]])}
        scores = {k: [] for k in matrices}
        if words:
            scores['words'] = []
        for train, test in GroupKFold(5).split(ids, y, groups[ids]):
            for name, x in matrices.items():
                model, xt = fit_scaled(x, y, train, test, check)
                scores[name].append(float(roc_auc_score(y[test], model.decision_function(xt))))
            if words:
                check()
                texts = frame.hidden_emo_text.to_numpy()[ids]
                v = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)
                model = LogisticRegression(C=10, max_iter=2000).fit(v.fit_transform(texts[train]), y[train])
                if np.any(model.n_iter_ >= model.max_iter):
                    raise RuntimeError('Word control did not converge')
                scores['words'].append(float(roc_auc_score(y[test], model.decision_function(v.transform(texts[test])))))
        row = {k: float(np.mean(v)) for k, v in scores.items()}
        row['gain_from_needs'] = row['ratings+needs']-row['ratings']
        from ...packs.trigger import TAGS
        gap = (needs[ids][y == 1].mean(0)-needs[ids][y == 0].mean(0))/(needs[ids].std(0)+1e-9)
        row['need_gaps_sd'] = dict(zip(TAGS, map(float, gap)))
        twins[pair] = row
    macro = {k: [] for k in ('ratings', 'needs', 'ratings+needs')}
    for train, test in GroupKFold(5).split(ratings, labels, groups):
        for name, x in (('ratings', ratings), ('needs', needs), ('ratings+needs', np.column_stack([ratings, needs]))):
            model, xt = fit_scaled(x, labels, train, test, check)
            macro[name].append(float(f1_score(labels[test], model.predict(xt), average='macro')))
    gains = [v['gain_from_needs'] for v in twins.values()]
    standardized = (needs-needs.mean(0))/(needs.std(0)+1e-9)
    profiles = {label: dict(zip(TAGS, map(float, standardized[labels == label].mean(0)))) for label in sorted(set(labels))}
    return {'twins': twins, 'thirteen_labels_macro_f1': {k: float(np.mean(v)) for k, v in macro.items()},
            'label_profiles_sd': profiles,
            'mean_gain': float(np.mean(gains)), 'pairs_ge_03': sum(g >= .03 for g in gains),
            'transfer_passed': float(np.mean(gains)) >= .06 and sum(g >= .03 for g in gains) >= 4,
            'protocol': 'five GroupKFold writer folds; mean of fold AUCs; training-only scale; same as supplied preflight'}
