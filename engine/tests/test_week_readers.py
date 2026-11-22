import sys
from pathlib import Path

import numpy as np

from tompathy_engine.eval.readers import week_anxiety as anxiety

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from week_blog_inputs import windows
from tompathy_engine.eval.readers.week_curve import choose_endpoint, factor_inverse, fixed_profile, nested_indices


def test_whole_post_windows():
    words = ['word']*110+['ends.']+['next']*65
    assert [len(w.split()) for w in windows(words)] == [111,65]
    assert ' '.join(windows(words)).split() == words
    assert list(windows([])) == []
    assert len(list(windows(['long']*3100))) == 20


def test_word_contrasts_are_paired_and_directional(monkeypatch):
    labels = [w for group in anxiety.GROUPS for w in group]+['other']
    a = np.array([1.,.2,-1.,.3])
    tags = np.array([a,a,-a,-a,-a,a,a,-a])
    rates = np.array([8,8,2,2,2,8,8,3])
    monkeypatch.setattr(anxiety,'resamples',lambda n:np.ones((45,n)))
    est=anxiety.estimate(np.tile(tags,(4,1)), labels*4, np.repeat(np.arange(4),len(labels)),
                         np.tile(rates,4),np.full(32,10),lambda:None)
    np.testing.assert_allclose(est['profileDifference']['interval'],[-2,-2])
    np.testing.assert_allclose(est['timeGapDifference']['interval'],[.6,.6])


def test_table_six_factor_fit_and_real_style_order():
    from cb_tables import design
    vocab=[f'form{i}' for i in range(50)]
    topics=[f'topic{i}' for i in range(300)]
    x=design(['Some words Here'],vocab,topics)
    assert x.shape==(1,358)
    np.testing.assert_allclose(x[0,57],2/3)
    # For a diagonal covariance with known positive diagonal, the fitted inverse is exact.
    s=np.diag([.2,.5,1.1])
    inv,_=factor_inverse(s,np.full(3,.05))
    np.testing.assert_allclose(inv,np.diag(1/s.diagonal()),atol=1e-12)


def test_nested_date_splits_and_curve_ceiling():
    ids=list('abcdefgh')
    left,right=nested_indices(['1','1','2','2','3','3','4','4'],ids)
    assert set(left)==set(range(4)) and set(right)==set(range(4,8))
    assert choose_endpoint({5:{'firstTen':.89,'firstOne':.5},10:{'firstTen':.9,'firstOne':.75}},
                           [5,10])==('firstOne',10)
    np.testing.assert_allclose(fixed_profile(.2,20),.5)
