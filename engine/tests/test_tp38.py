import numpy as np

from tompathy_engine.eval.readers.tp38 import lifts, unit_stats


def test_weighted_removal_matches_explicit_controls_and_excludes_unknowns():
    scores = np.array([.95,.25,.7,.1,.3,.85,.12,.15,.01])
    words = np.array(['ashamed','ashamed','guilty','guilty','guilty','other','other','other','other'])
    food = np.array([1,0,1,0,-1,1,0,0,-1])
    weights = np.array([1,1,1,1,1,3,3,3,3])
    result = lifts(unit_stats(scores,words,food,weights).sum(axis=0))[0]
    for idx,(mask,w) in enumerate([(food>=0,weights),(food==0,weights),
                                   (food>=0,np.ones(len(food),int)),(food==0,np.ones(len(food),int))]):
        duplicated = np.repeat(np.flatnonzero(mask),w[mask])
        for j,label in enumerate(('ashamed','guilty')):
            sample=scores[duplicated];inside=words[duplicated]==label
            expected=(sample[inside].mean()-sample[~inside].mean())/sample.std()
            np.testing.assert_allclose(result[idx,j],expected)
