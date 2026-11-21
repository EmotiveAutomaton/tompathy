import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
import word_table_tp24_mixed as study


def test_selected_reader_missing_data_and_common_denominator():
    ids=['only-b','both','only-trained','neither']
    ratings=np.full((4,len(study.FEATURES)),np.nan)
    ratings[:2]=2
    trained=np.arange(len(study.FEATURES),dtype=float)
    slots={key:('B' if i in (0,2) else 'trained') for i,key in enumerate(study.FEATURES)}
    _,mixed,masks=study.mixed_features(ids,ratings,{'only-trained':trained+1,'both':trained},slots)
    assert np.array_equal(mixed[1],np.where([slots[f]=='B' for f in study.FEATURES],2,trained))
    assert mixed[0,0]==2 and np.isnan(mixed[0,1])
    assert np.isnan(mixed[2,0]) and mixed[2,1]==trained[1]+1 and np.isnan(mixed[3]).all()
    assert masks['common'].tolist()==[False,True,False,False]
    assert sum(masks['prompted'])==sum(masks['trained'])==2


class SavedFold:
    def __init__(self,root):
        self.root=root
        self.files={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}

    def artifact(self,name):
        assert name in self.files
        return self.root/name


def test_registered_fold_excludes_reserved_and_catches_wrong_order(tmp_path):
    prefix=tmp_path/'rung-0/rd2-trained/fold-0'
    prefix.mkdir(parents=True)
    (prefix/'complete.json').write_text(json.dumps({'rows':3,'selectedSeed':23}))
    (prefix/'selection.json').write_text(json.dumps({'selected':{'seed':23}}))
    ratings=np.arange(3*len(study.RATINGS),dtype=float).reshape(3,-1)
    np.savez(prefix/'forecasts-0000.npz',ratings=ratings,ids=['b','a','sealed'],F2=[False,False,True])
    mirror=SavedFold(tmp_path)
    rows,status=study.fold_forecasts(mirror,0,['b','a'],{'sealed'})
    assert status=='complete' and list(rows)==['b','a']
    assert rows['a'].tolist()==[ratings[1,study.RATINGS.index(f)] for f in study.FEATURES]
    assert study.fold_forecasts(mirror,1,[],set())==({},'unfinished')
    with pytest.raises(ValueError,match='writer-fold roster'):
        study.fold_forecasts(mirror,0,['a','b'],{'sealed'})
    with pytest.raises(ValueError,match='reserved'):
        study.fold_forecasts(mirror,0,['b','a'],{'other'})
    with pytest.raises(ValueError,match='registered partition'):
        study.fold_forecasts(mirror,0,['b','a'],{'sealed','missing'},require_reserved=True)
