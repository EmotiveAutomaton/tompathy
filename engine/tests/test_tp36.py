import numpy as np

from tompathy_engine.eval.readers.tp36 import movement, statistic, tag_weights
from tompathy_engine.packs.trigger import TAGS


def test_four_movements_preserve_exact_threshold_ties():
    matrix = np.array([[1, 1], [-1, 1], [.5, 1], [0, -.5]],float)
    result = movement(matrix, np.array([.1,.2,.3,.4]))
    np.testing.assert_allclose([val[0,1] for val in result], [.1,.2,.3,.4])


def test_merged_belonging_uses_each_tag_once_and_weighted_rows_match_repetition():
    transform = tag_weights()
    assert {TAGS[i] for i in np.flatnonzero(transform[:,6])} == {'family','contact','belonging','idealism'}
    np.testing.assert_allclose(transform[transform[:,6]>0,6],.25)
    x = np.random.default_rng(23).normal(size=(40,len(TAGS)))
    counts = np.arange(40)%3
    result = statistic(x,x*x,transform,counts)
    expanded = np.repeat(x,counts,axis=0)
    z = (expanded-expanded.mean(axis=0))/expanded.std(axis=0)
    score = z@transform
    np.testing.assert_allclose(result[:,:,0],np.corrcoef(score,rowvar=False),atol=1e-12)
