"""Verified corpus readers; text and writer identifiers never enter aggregates."""
import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ...packs.registry import sha256


def verify(root, intake_name='intake.json'):
    root=Path(root)
    manifest=json.loads((root/intake_name).read_text(encoding='utf8'))
    for name,pin in manifest['files'].items():
        path=(root/name).resolve()
        if not path.is_relative_to(root.resolve()) or path.is_symlink() or sha256(path)!=pin:
            raise ValueError('Corpus intake binding differs')
    return {'intakePin':sha256(root/intake_name),'license':manifest['license_as_read'],
            'research_only':manifest['research_only'],'counts':manifest['counts']}


def ed_situations(root):
    root=Path(root)
    intake='intake-v2.json' if (root/'intake-v2.json').exists() else 'intake.json'
    identity=verify(root,intake)
    records=[]
    for split in ('train','valid','test'):
        with (root/f'{split}.csv').open(encoding='utf8',newline='') as stream:
            rows=list(csv.DictReader(stream,quoting=csv.QUOTE_NONE))
        first=[r for r in rows if r['utterance_idx']=='1']
        if len(first)!=len({r['conv_id'] for r in rows}):
            raise ValueError('Exactly one initial situation per dialogue required')
        for r in first:
            if not r['speaker_idx'].isdigit():
                raise ValueError('Malformed situation writer')
            records.append({'id':r['conv_id'],'text':r['prompt'].replace('_comma_',','),
                            'label':r['context'],'writer':r['speaker_idx'],'source_split':split})
    frame=pd.DataFrame(records)
    if len(frame)!=24850 or frame.id.duplicated().any() or frame.label.nunique()!=32:
        raise ValueError('EmpatheticDialogues census differs')
    return frame,identity


def go_comments(root):
    root=Path(root)
    identity=verify(root)
    labels=(root/'emotions.txt').read_text(encoding='utf8').splitlines()
    raw=pd.concat([pd.read_csv(root/f'goemotions_{i}.csv',keep_default_na=False,
        usecols=['id','text','author',*labels]) for i in (1,2,3)],ignore_index=True)
    if (raw.groupby('id').text.nunique()>1).any() or (raw.groupby('id').author.nunique()>1).any():
        raise ValueError('Comment IDs have conflicting source text or authors')
    unique=raw.drop_duplicates('id')[['id','text','author']].reset_index(drop=True)
    indices=dict(zip(unique.id,range(len(unique))))
    text_by_id=dict(zip(unique.id,unique.text))
    truth=np.zeros((len(unique),len(labels)),dtype=np.int8)
    source=np.full(len(unique),'unreleased',dtype=object)
    for split in ('train','dev','test'):
        with (root/f'{split}.tsv').open(encoding='utf8',newline='') as stream:
            for text,label_ids,ident in csv.reader(stream,delimiter='\t'):
                i=indices[ident]
                if source[i]!='unreleased' or text!=text_by_id[ident]:
                    raise ValueError('Published split text or membership differs from raw comments')
                source[i]=split
                truth[i,[int(x) for x in label_ids.split(',')]]=1
    unique['writer']=unique.author.fillna('')
    unique['writer_known']=~unique.writer.isin(['','[deleted]','[removed]'])
    unique['source_split']=source
    identity.update(published_labelled=int((source!='unreleased').sum()),
                    writer_unknown=int((~unique.writer_known).sum()),
                    raw_unlabelled_policy='Features can be read for every raw comment; label-group tests use released consensus labels only')
    return unique.drop(columns='author'),truth,labels,identity
