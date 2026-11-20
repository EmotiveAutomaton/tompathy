import numpy as np
import pytest

from tompathy_engine.eval.readers import tp31_student as student
from tompathy_engine.eval.readers.tp31_teacher import SOURCES


def test_missing_class_cannot_pass_source_gate():
    assert student.rates([1, 1], [.9, .9], .5)['silence'] is None
    assert not student.rates([0, 0], [.1, .1], .5)['passes']
    assert not student.rates([1, 0], [.9, .9], .5)['passes']


def test_threshold_uses_all_development_sources_and_fixed_fallback():
    y = [1, 0, 1, 0]
    threshold, valid, _ = student.threshold_on_development(y, [.9, .1, .9, .1], ['a','a','b','b'], {'a','b'})
    assert valid and threshold == pytest.approx(.15)
    threshold, valid, curves = student.threshold_on_development(y, [.9, .1, .1, .9], ['a','a','b','b'], {'a','b'})
    assert not valid and threshold == .5 and set(curves) == {'a','b'}


def test_source_separation_removes_alias_overlap_and_preserves_groups():
    rows = [{'id': f'{s}-{i}', 'source': s, 'group': f'{s}-{i//2}', 'text': f'{s} sentence {i}'}
            for s in SOURCES for i in range(20)]
    rows[20]['text'] = '  COAUTHOR SENTENCE 0  '
    index = student.fitting_indices(rows, 'coauthor')
    assert index['excludedTextOverlaps'] == 1 and 20 not in index['refit']
    assert not set(index['test']) & set(index['refit'])
    assert not {rows[i]['group'] for i in index['fit']} & {rows[i]['group'] for i in index['development']}


def test_fold_fits_without_held_vectors_or_target_leakage(monkeypatch):
    rows = [{'id': f'{s}-{i}', 'source': s, 'group': f'{s}-{i//2}', 'text': f'{s} sentence {i}'}
            for s in SOURCES for i in range(20)]
    truth = np.array([i%2 for i in range(len(rows))])
    vectors = np.column_stack((truth, np.arange(len(rows))))
    fits = []
    class Model:
        coef_ = np.array([[1., 0.]])
        intercept_ = np.array([0.])
        def predict_proba(self, x):
            probability = .1+.8*x[:, 0]
            return np.column_stack((1-probability, probability))
    def fit(x, y, check):
        fits.append(x[:, 1].astype(int).tolist());return Model()
    monkeypatch.setattr(student, 'fit', fit)
    result = student.fit_source_fold(rows, truth, vectors, 'ed', lambda: None)
    assert result['qualifies'] and len(result['probability']) == 20
    assert all(rows[i]['source'] != 'ed' for ids in fits for i in ids)


def test_acceptance_retains_exact_sizes_and_integer_boundaries():
    result = student.acceptance([.1]*32+[.9]*8, [.1]*153+[.9]*38, .5)
    assert result['passes']
    assert not student.acceptance([.1]*31+[.9]*9, [.1]*191, .5)['passes']
    assert not student.acceptance([.1]*40, [.1]*152+[.9]*39, .5)['passes']
    with pytest.raises(ValueError):
        student.acceptance([.1]*39, [.1]*191, .5)
