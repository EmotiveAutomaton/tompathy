import sys
from pathlib import Path

import numpy as np

from tompathy_engine.eval.readers import week_anxiety as anxiety

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from week_blog_inputs import windows


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
