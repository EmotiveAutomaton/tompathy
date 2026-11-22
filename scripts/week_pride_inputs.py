"""Prepare the separate PRIDE fit from TP30 partitions and saved frozen vectors."""
import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

from cb_inputs import pin
from tompathy_engine.eval.readers.affect_data import verify
from tompathy_engine.eval.readers.tp39 import saved
from tompathy_engine.eval.readers.tp40 import MANIFEST
from tompathy_engine.eval.readers.word_panels import pinned

FROZEN = Path('.local/nine-channel/tp30-frozen-a')
SOURCE = 'd04658e1c84ef10e0c95847947359b24da91b79368bd91b3fa22da2d70c3e250'


def prepare(out, check):
    old = pinned(FROZEN/'receipt.json', SOURCE)
    data = Path('.local/readers/data')
    go = data/'go-emotions'
    if verify(go)['intakePin'] != old['sources']['go']['intakePin']:
        raise ValueError('Go source identity differs')
    ev = data/'crowd-enVent2023/corpus/crowd-enVent_validation.tsv'
    if pin(ev) != old['sources']['envent']['files']['validation']:
        raise ValueError('Event validation source differs')
    votes = pd.concat([pd.read_csv(go/f'goemotions_{i}.csv', usecols=['id','pride'],
                                   dtype={'id':str}) for i in (1,2,3)])
    raters = pd.read_csv(ev,sep='\t',quoting=3,usecols=['text_id','emotion'],dtype=str)
    if len(votes) != 211225 or len(raters) != 6000 or 'pride' not in set(raters.emotion):
        raise ValueError('Original rater census or pride label differs')
    shares = {'go':votes.groupby('id').pride.mean(),
              'envent':raters.emotion.eq('pride').groupby(raters.text_id).mean()}
    dest = out/'spark-inputs'
    dest.mkdir()
    counts = {}
    with np.load(saved(FROZEN,'vectors.npz',old),allow_pickle=False) as vectors:
        for source in ('go','envent','ed'):
            check()
            x = vectors[source]
            if source != 'ed':
                with np.load(saved(FROZEN,source+'-targets.npz',old),allow_pickle=False) as a:
                    ids, train = a['ids'].astype(str), a['train']
                y = shares[source].reindex(ids).to_numpy()
                if (len(x) != len(y) or not np.isfinite(y[train]).all()
                        or set(shares[source].index)-set(ids)):
                    raise ValueError('Pride shares differ from frozen partition')
                prior = y[train]
                counts[source] = dict(rated=int(np.isfinite(y).sum()),positive=int((y>0).sum()),
                                      fitted=len(prior),fittedPositive=int((prior>0).sum()))
                np.savez(dest/(source+'-fit.npz'),x=x[train],y=prior)
            path = saved(FROZEN,source+'-profile-forecasts.npz',old)
            with np.load(path,allow_pickle=False) as a:
                nine = a['probabilities']
                if source=='go':
                    with np.load(saved(FROZEN,'go-targets.npz',old),allow_pickle=False) as g:
                        x=x[g['test']]
                        if not np.array_equal(g['ids'][g['test']],a['ids']):
                            raise ValueError('Original held-out comments differ')
                if nine.shape!=(len(x),9):
                    raise ValueError('Misaligned original channels')
                np.savez(dest/(source+'-forecast.npz'),x=x,nine=nine)
    # Text only, in the two original roster orders. All local joins use the pinned rosters.
    pt = Path('.local/person-teacher/inputs')
    manifest = pinned(pt/'manifest.json',MANIFEST)
    for block,h in manifest['files'].items():
        rows=pinned(pt/(block+'.json'),h)
        with gzip.open(dest/(block+'-sentences.jsonl.gz'),'xt',encoding='utf8') as stream:
            for row in rows:
                stream.write(json.dumps(row['text'],ensure_ascii=False)+'\n')
    return dict(source=SOURCE,sentenceManifest=MANIFEST,counts=counts,
                files={p.name:pin(p) for p in sorted(dest.iterdir())})
