import numpy as np
import pandas as pd

from tompathy_engine.eval.readers.tp35 import WriterMoments, slopes


def test_cluster_moments_match_explicitly_repeated_writers_and_weighted_ols():
    rng = np.random.default_rng(47)
    x = rng.normal(size=(90, 4))
    y = x @ [1.2, -.7, .2, .1] + rng.normal(size=90)
    data = pd.DataFrame(x, columns=list('abcd'))
    data['y'] = y
    data['writerIndex'] = np.repeat(np.arange(30), 3)
    data['w'] = rng.uniform(.2, 1, 90)
    moments = WriterMoments(data, list('abcdy'), 'w')
    multiplicity = rng.integers(0, 5, 30)
    mass, corr, sd = moments.correlation(multiplicity[None])
    weight = data.w.to_numpy() * multiplicity[data.writerIndex]
    raw = np.column_stack([x, y])
    mu = np.average(raw, axis=0, weights=weight)
    z = raw - mu
    sigma = np.sqrt(np.average(z*z, axis=0, weights=weight))
    z = z/sigma * np.sqrt(weight[:,None])
    expected = np.linalg.lstsq(z[:,:4], z[:,4], rcond=None)[0][0]
    np.testing.assert_allclose(slopes(corr, 4)[0,0], expected)
    np.testing.assert_allclose(sd[0], sigma)
    np.testing.assert_allclose(mass[0], weight.sum())


def test_constant_predictor_is_unestimable():
    data = pd.DataFrame({'x':[1,1,1], 'y':[1,2,3], 'writerIndex':[0,1,2]})
    _, corr, _ = WriterMoments(data, ['x','y']).correlation(np.ones((1,3)))
    assert np.isnan(slopes(corr, 1)).all()
