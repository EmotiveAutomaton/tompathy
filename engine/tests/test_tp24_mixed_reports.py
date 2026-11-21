import json

import numpy as np
import pytest
from sklearn.model_selection import GroupKFold
from tompathy_engine.eval.readers import tp24_mixed as study


def test_comparison_uses_same_complete_reports_and_keeps_selected_values(tmp_path,monkeypatch):
    ids = np.array(['c','a','b'])
    mixed = np.arange(24,dtype=float).reshape(3,8)
    prompted = mixed+1
    prompted[1,0] = np.nan
    archive = tmp_path/'features.npz'
    receipt = tmp_path/'receipt.json'
    def store(mask):
        np.savez(archive,reportIds=ids,cohorts=['Q2','Q1','SP1'],features=study.FEATURES,
                 trained=mixed-1,prompted=prompted,mixed=mixed,common=mask)
        receipt.write_text(json.dumps({'archivePin':study.sha256(archive),'coverage':{'common':2}}))
        monkeypatch.setitem(study.ROSTERS,'initial',study.sha256(receipt))
    store([True,False,True])
    _, kept, groups, views = study.common_rows(tmp_path,'initial')
    assert kept.tolist() == ['c','b'] and groups.tolist() == ['Q2','SP1']
    np.testing.assert_array_equal(views['mixed'],mixed[[0,2]])
    store([True,True,False])
    with pytest.raises(ValueError,match='denominator'):
        study.common_rows(tmp_path,'initial')


def test_fixed_table_scales_on_other_writers_and_disables_failed_tense():
    rng = np.random.default_rng(23)
    writers = np.repeat(np.arange(10),3)
    slots = rng.normal(size=(30,27)) + writers[:,None]
    when = rng.integers(0,2,size=(30,2))
    words = np.resize(study.LOSS,30)
    actual = study.table_profile(slots,when,words,writers,False,lambda:None)
    matrix = np.column_stack((slots,when))
    for train,test in GroupKFold(5).split(matrix,words,writers):
        assert set(writers[test]).isdisjoint(writers[train])
        scaled = (matrix[test]-matrix[train].mean(0))/(matrix[train].std(0)+1e-9)
        np.testing.assert_allclose(actual[test],study.table_scores(scaled,False))
    np.testing.assert_allclose(actual,study.table_profile(slots,1-when,words,writers,False,lambda:None))


def test_disagreements_keep_table_to_profile_direction_and_top_ties():
    table = np.array([[0,0,1,1,0],[0,1,0,0,0]],float)
    fitted = np.array([[0,0,0,0,1],[0,1,0,0,0]],float)
    result = study.profile_comparison(table,fitted)
    assert result['channels'][2]=='SADNESS'
    assert result['n']==2 and result['disagreements']==1 and result['agreement']==.5
    assert result['tableByTP30'][2][4]==1 and result['tableByTP30'][4][2]==0
    assert result['tableTopTies']==1 and result['perChannelSpearman']['RAGE'] is None
