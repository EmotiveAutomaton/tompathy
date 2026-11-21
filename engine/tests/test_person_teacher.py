"""Constructed cases for missing answers, word means and held-out writer matching."""
import numpy as np
import pandas as pd

from tompathy_engine.eval.readers import person_halves as halves
from tompathy_engine.eval.readers import tp40


def test_word_means_exclude_all_of_the_same_writer_even_in_the_other_half():
    words=np.array(['a']*6+['b']*6)
    writers=np.array(['u','u','v','v','z','z']*2)
    owner=np.array([0,0,1,1,-1,-1]*2)
    half=np.array([0,1,0,1,-1,-1]*2)
    values=np.array([10,14,2,6,0,4]*2,float)[:,None]
    got=halves.half_departures(values,words,writers,owner,half)
    assert np.allclose(got[:,:,0],[[7,-5],[11,-1]])


def test_sorted_halves_are_balanced_and_stable_under_input_permutation():
    writers=np.repeat(['u','v','z'],[9,8,7])
    ids=np.array([str(i) for i in range(len(writers))])
    order=np.arange(len(ids))[::-1]
    names,owner,h=halves.split(writers,ids)
    names2,owner2,h2=halves.split(writers[order],ids[order])
    assert names==names2 and np.array_equal(owner,owner2[order]) and np.array_equal(h,h2[order])
    assert sorted(np.bincount(h[writers=='u']).tolist())==[4,5]
    assert np.all(owner[writers=='z']==-1)


def test_likelihood_picks_repeated_distinct_writers_and_honors_tie_order():
    rng=np.random.default_rng(10)
    a=rng.normal(size=(64,12))
    p=np.stack([a,a.copy()])
    sets={'style':[0,1,2],'channels':[3,4,5],'tags':[6,7,8],'features':[9,10,11]}
    match,_=halves.match(p,sets,halves.resamples(64,64),lambda:None)
    assert match['all']['likelihood']['10']['value']==1
    assert match['all']['squaredDistance']['1']['value']==1
    assert halves.ranks(np.zeros((4,4))).tolist()==[1,2,3,4]


def test_correlation_pairs_keep_missing_writers_out_and_retain_negative_sign():
    a=np.array([[1.],[2.],[3.],[np.nan]])
    b=np.array([[5.],[3.],[1.],[9.]])
    assert np.allclose(halves.correlations(a,b,np.ones((1,4))),-1)


def test_unknown_never_counts_as_no_change_and_disagreement_is_paired():
    yes={'change':True,'whose':'writer','when':'ahead'}
    no={'change':False,'whose':'nobody','when':'none'}
    r=tp40.summarize_text([no,None],[yes,no])
    assert (r['noChange'],r['unknownTexts'],r['paired'],r['changeDisagree'])==(0,1,1,1)
    assert np.isnan(r['ownShare'])
    r=tp40.summarize_text([yes,None],[yes,None])
    assert r['unknownTexts']==0 and r['noChange']==0
    r=tp40.summarize_text([yes,no],[no,no])
    assert r['changeShare']==r['ownShare']==r['aheadShare']==.5


def test_ratio_uses_word_condition_and_resamples_whole_writers():
    no={'change':False,'whose':'nobody','when':'none'}
    yes={'change':True,'whose':'writer','when':'ahead'}
    rows=[]
    for i in range(8):
        for word,standing,group in [('standingword',True,[no,no,no,yes]),('otherword',False,[yes,no,yes,yes])]:
            for b in group:
                rows.append({'writer':str(i),'word':word,'standing':standing,**tp40.summarize_text([b],[b])})
    table,ratio,_=tp40.source_table(pd.DataFrame(rows),lambda:None)
    assert ratio['value']==3 and ratio['interval']==[3,3] and ratio['passes']
    assert table['standing']['textNoChange']['value']==.75
