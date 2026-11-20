import numpy as np
import pytest

from tompathy_engine.eval.readers.spark_panel import compare_first_passes


def inputs():
    truth = np.array([[1+i%5]*8 for i in range(300)])
    return truth.tolist(), (6-truth).tolist(), truth, truth.astype(float)


def test_common_first_pass_mask_and_selection_preserve_original_gate_failure():
    a, b, truth, baseline = inputs()
    a[0] = None
    b[1] = None
    row = compare_first_passes(a, b, truth, baseline, {'a': False, 'b': True})
    assert row['commonValid'] == 298 and row['selectedRole'] == 'a'
    assert row['scores']['a']['meanSpearman'] == pytest.approx(1)
    assert row['scores']['b']['meanSpearman'] == pytest.approx(-1)
    assert not row['selectedReaderQualified']


def test_constant_or_missing_comparison_does_not_manufacture_a_winner():
    a, b, truth, baseline = inputs()
    row = compare_first_passes(a, [[3]*8]*300, truth, baseline, {'a': True, 'b': False})
    assert row['selectedRole'] is None
    assert row['scores']['b']['meanSpearman'] is None
    row = compare_first_passes([None]*300, b, truth, baseline, {'a': False, 'b': True})
    assert row['commonValid'] == 0 and row['selectedRole'] is None


def test_fixed_tie_break_and_no_rating_coercion():
    a, _, truth, baseline = inputs()
    assert compare_first_passes(a, a, truth, baseline, {'a': True, 'b': True})['selectedRole'] == 'a'
    a[0][0] = True
    with pytest.raises(ValueError, match='integer ratings'):
        compare_first_passes(a, a, truth, baseline, {'a': True, 'b': True})
