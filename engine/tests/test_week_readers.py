import sys
from pathlib import Path

import numpy as np

from tompathy_engine.eval.readers import week_anxiety as anxiety

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from week_blog_inputs import windows
from tompathy_engine.eval.readers.week_curve import choose_endpoint, factor_inverse, fixed_profile, nested_indices


def test_worry_language_uses_long_posts_and_requires_variable_within_author():
    from week_worry_language import author_slope,post_status

    row={"qualifies":True,"words":300,"opening":"digest","suffixWords":150,"suffixFirstPerson":3}
    assert post_status(row)=="eligible"
    assert post_status(dict(row,words=299))=="outside"
    assert post_status(dict(row,opening=None))=="noOpening"
    w=np.arange(10.)
    np.testing.assert_allclose(author_slope(w,1-.01*w),-1.)
    assert author_slope(w[:9],w[:9]) is None and author_slope(w,np.ones(10)) is None


def test_stability_compares_the_paired_median_tag_in_every_draw(monkeypatch):
    import week_worry_language as study

    x=np.tile(np.arange(9.)[:,None],(1,20))
    y=x.copy();y[:,1:]*=-1
    monkeypatch.setattr(study,"resamples",lambda n:np.ones((79,n)))
    row=study.stability(x,y,lambda:None)
    np.testing.assert_allclose(row["worryMinusMedianTag"]["interval"],[2.,2.])


def test_competence_separates_opposite_within_and_between_effects(monkeypatch):
    import week_competence as study

    n=7
    writers=np.repeat(np.arange(n,dtype=float),6)
    occasion=np.tile([-1,0,1,-1,0,1],n)
    values=np.tile((writers+occasion)[:,None],(1,len(study.NAMES)))
    values[:,study.NAMES.index("competence")]=writers-occasion
    groups=np.arange(6*n).reshape(n,6)
    halves=np.tile([0,0,0,1,1,1],(n,1))
    monkeypatch.setattr(study,"resamples",lambda n:np.ones((63,n)))
    rows=study.paired_measures(values,groups,halves,lambda:None)
    np.testing.assert_allclose(rows["readings"]["within"]["curiosity"]["competence"]["interval"],[-1,-1])
    np.testing.assert_allclose(rows["readings"]["between"]["curiosity"]["competence"]["interval"],[1,1])
    assert rows["perLineVerdicts"]["curiosityBetweenAtLeastPointThree"]


def test_competence_keeps_empty_q19_prefix_and_rejects_misaligned_features():
    import pytest
    from week_competence import FEATURES, TAGS, source_table

    tags = np.empty((0, len(TAGS)))
    features = np.empty((0, len(FEATURES)))
    result = source_table(tags, features, [], [], [], lambda: None)
    assert result["status"] == "insufficient writers"
    assert result["support"]["sourceRows"] == 0
    with pytest.raises(ValueError, match="Misaligned"):
        source_table(tags, features[:, :-1], [], [], [], lambda: None)


def test_care_article_fallback_removes_both_writer_and_article_levels():
    from week_care_read import indicators, slopes

    writer=np.repeat(np.arange(6),5)
    article=np.tile(np.arange(5),6)
    rng=np.random.default_rng(23)
    predictors=rng.normal(size=(30,2))
    weights=np.tile([2,1,0,1,2],6).astype(float)
    mu=np.average(predictors,weights=weights,axis=0)
    sd=np.sqrt(np.average((predictors-mu)**2,weights=weights,axis=0))
    x=((predictors-mu)/sd).mean(axis=1)
    y=np.column_stack((2*x+writer+5*article,3*x-writer+article))
    design=indicators(writer,article)
    np.testing.assert_allclose(slopes(design,predictors,y,weights),[2,3,1],atol=1e-8)
    assert np.isnan(slopes(design,np.ones_like(predictors),y,weights)).all()


def test_release_probe_waits_locally_and_recovers_from_timeout(monkeypatch):
    from pathlib import Path
    import week_followthrough as monitor
    calls=[]
    accepted=False
    monkeypatch.setattr(Path,'is_file',lambda p: p.name=='earlier-accepted.json' and accepted)
    def timeout(*args,**kwargs):
        calls.append(1)
        raise monitor.subprocess.TimeoutExpired('ssh',30)
    monkeypatch.setattr(monitor.subprocess,'run',timeout)
    assert not monitor.transfer('Q20') and not calls
    accepted=True
    assert not monitor.transfer('Q20') and len(calls)==1


def test_word_departures_require_two_clean_controls_on_each_side():
    from week_word_departures import author_cells, matches

    assert matches("unhappy proudly")==0
    assert matches("Sad sadness; scared!")==5
    tags=np.arange(20.).reshape(10,2)
    masks=np.array([matches(s) for s in ["sad","sadness","anger","hello","ok"]*2])
    cells=author_cells(tags,masks,([0,1,2,3,4],[5,6,7,8,9]))
    assert list(cells)==["sad"] and cells["sad"][0]==2
    np.testing.assert_allclose(cells["sad"][1][1],tags[[3,4]].mean(0))
    assert not author_cells(tags,masks,([0,1,2,3],[5,6,7,8,9]))


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


def test_table_six_retains_signal_in_the_58th_style_reading():
    from tompathy_engine.eval.readers.week_curve import table_six
    fold=np.repeat([0,1],8)
    common=np.tile([-1.,1.],8)
    capitalization=np.tile([-1.,-1.,1.,1.],4)
    controls=np.tile(common[:,None],(1,358))
    controls[:,57]=capitalization
    tags=np.tile(capitalization[:,None],(1,19))
    result=table_six((controls,controls),(tags,tags),fold,lambda:None,draws=4)
    assert result['status']=='descriptive'
    cross=np.asarray(result['cA'])
    assert cross.shape==(358,19)
    np.testing.assert_allclose(cross[57],1.)
    np.testing.assert_allclose(np.delete(cross,57,axis=0),0.)
    np.testing.assert_allclose(result['lines']['diagonal']['pooled']['value'],0.,atol=1e-12)


def test_nested_date_splits_and_curve_ceiling():
    ids=list('abcdefgh')
    left,right=nested_indices(['1','1','2','2','3','3','4','4'],ids)
    assert set(left)==set(range(4)) and set(right)==set(range(4,8))
    assert choose_endpoint({5:{'firstTen':.89,'firstOne':.5},10:{'firstTen':.9,'firstOne':.75}},
                           [5,10])==('firstOne',10)
    np.testing.assert_allclose(fixed_profile(.2,20),.5)


def test_teacher_rank_intervals_recompute_discrete_ties(monkeypatch):
    from scipy.stats import spearmanr
    import week_teacher_read as teacher
    x=np.array([0,0,1,2,2,3.]);y=np.array([1,1,1,3,4,2.])
    owners=np.array([0,1,0,1,0,1])
    monkeypatch.setattr(teacher,'resamples',lambda n:np.tile([2.,0.],(80,1)))
    stats=teacher.rank_interval(x,y,owners,lambda:None)
    np.testing.assert_allclose(stats['value'],spearmanr(x,y).statistic)
    np.testing.assert_allclose(stats['interval'],spearmanr(x[owners==0],y[owners==0]).statistic)


def test_sentence_contrasts_keep_the_tenth_head_and_unavailable_results():
    from week_display import NAMES,move_table
    diffs=np.full((3,10),2.)
    diffs[:,NAMES.index('DISGUST')]=1.
    table=move_table(diffs,lambda:None)
    assert table['allTenPositive'] and table['disgustLeast'] and table['disgustBelowMedian']
    assert table['disgustMinusMedian']['interval']==[-1.,-1.]
    diffs[:,-1]=np.nan
    partial=move_table(diffs,lambda:None)
    assert not partial['allTenPositive'] and partial['outputs']['PRIDE']['validDraws']==0
    assert move_table(diffs[:0],lambda:None)['disgustMinusMedian']['value'] is None


def test_omitted_head_scores_use_the_original_matching_operator():
    from week_need_losses import omission_hits
    from tompathy_engine.eval.readers.week_curve import rank_arms
    rng=np.random.default_rng(64)
    a=rng.normal(size=(60,377))
    b=rng.normal(size=a.shape)
    b[:,358:]=a[:,358:]+rng.normal(size=(60,19))*.3
    fold=np.arange(len(a))%2
    omitted=[7,10]
    hits=omission_hits(a,b,fold,{'pair':omitted},lambda:None)
    ref=rank_arms(a,b,[slice(0,358),np.delete(np.arange(358,377),omitted)],fold,lambda:None)
    np.testing.assert_array_equal(hits['baseline'],ref[0]<=10)
    np.testing.assert_array_equal(hits['pair'],ref[1]<=10)


def test_highest_need_uses_author_pairing_and_shared_credit_for_ties():
    from week_need_losses import highest_need
    from tompathy_engine.packs.trigger import TAGS
    x=np.zeros((40,len(TAGS)))
    x[:20,TAGS.index('curiosity')]=1
    x[20:,TAGS.index('food')]=1
    groups={'Competence':['curiosity'],'Body':['food']}
    weights=np.ones((3,len(x)))
    paired=highest_need(x,x,groups,weights,lambda:None)
    assert paired['paired']==1 and .47<paired['dealt']<.53
    tied=highest_need(x*0,x*0,groups,weights,lambda:None)
    np.testing.assert_allclose(tied['difference']['value'],0,atol=1e-12)
