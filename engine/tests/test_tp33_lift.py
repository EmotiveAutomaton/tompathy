import pytest

from tompathy_engine.eval.readers.tp33 import lifted


def windows(values):
    return [{"from":i*5, "to":i*5+8, "value":v} for i,v in enumerate(values)]


def test_original_scale_threshold_and_page_median():
    assert lifted(windows([.25, .5, .625])) == [(10,18)]
    assert lifted(windows([.25, .5, .624])) == []
    assert lifted(windows([.95])) == []
    assert lifted(windows([.25,.5])) == [(5,13)]


def test_invalid_spans_and_scale():
    for data in ([], windows([1.01]), windows([float("nan")]), windows([.2])*2):
        with pytest.raises(ValueError):
            lifted(data)
