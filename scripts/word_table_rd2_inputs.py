"""Preregister the six prompt bodies and ordered development panel before reading scores."""
import json
import os
from pathlib import Path

from word_table_inputs import ROOT, ordered, pin, write
from word_table_lane import core, string_pin
from word_table_rd2 import FEATURES, prompts


def freeze(base):
    from tokenizers import Tokenizer
    from tompathy_engine.eval.readers.envent import load
    opening=json.loads((base/'intake-a/intake.json').read_bytes())
    named=base/'intake-a/spark/Q2.json'
    if pin(named)!=opening['jobs']['Q2']['filePin']:
        raise ValueError('Original training report set changed')
    input_rows=json.loads(named.read_bytes())
    data=load(ROOT/'.local/readers/data/crowd-enVent2023')
    reports={str(r.text_id):r for r in data.reports.itertuples()}
    training={r['id'] for r in input_rows}
    held={str(data.reports.iloc[i].text_id) for i in data.test}
    if len(training)!=5400 or training & held or training|held!=set(reports):
        raise ValueError('Report partitions differ')
    order=ordered(training,'RD2:ex:23:')
    example_ids=[key for band in ({1},{2,3},{4},{5}) for key in
                 [k for k in order if int(reports[k].standards) in band][:2]]
    examples=[{'id':k,'text':reports[k].hidden_emo_text,**{f:int(getattr(reports[k],f)) for f in FEATURES}}
              for k in example_ids]
    panel=ordered(training-set(example_ids),'RD2:23:')[:600]
    items=[{'id':k,'text':reports[k].hidden_emo_text} for k in panel]
    variants=prompts(core,examples)
    tk=base/'tokenizer-source/Q3-tokenizer.json'
    if pin(tk)!='5f9e4d4901a92b997e463c1f46055088b6cca5ca61a6522d1b9f64c4bb81cb42':
        raise ValueError('Bound tokenizer differs')
    tokenizer=Tokenizer.from_file(str(tk))
    dest=base/'rd2-input-a'
    dest.mkdir(exist_ok=False)
    write(dest/'G3.json',items)
    write(dest/'RD2-prompts.json',variants)
    lengths={v:{r['id']:len(tokenizer.encode(s['prompt']+r['text'],add_special_tokens=False).ids) for r in items}
             for v,s in variants.items()}
    write(dest/'RD2-lengths.json',lengths)
    write(dest/'local-development-key.json',[{'id':k,**{f:int(getattr(reports[k],f)) for f in FEATURES}} for k in panel])
    sheet=ROOT/'.local/readers/data/crowd-enVent2023/questionnaires/generation/round-9/strategy2_excludedtopics/anger.pdf'
    names=['G3.json','RD2-prompts.json','RD2-lengths.json']
    spec={'modules':['scripts/word_table_rd2.py'],'jobs':{'G3':{'rows':len(items),
          'files':{n:str(dest/n) for n in names}}},'pins':{n:pin(dest/n) for n in names},
          'provenance':{'sourcePins':data.pins,'questionnairePin':pin(sheet),'questionnairePrintedPages':[9,10],
                        'exampleIds':example_ids,'trainingPool':len(training),'reservedReportsInDevelopment':0,
                        'promptPins':{k:string_pin(v['prompt']) for k,v in variants.items()},
                        'tokenizerPin':pin(tk),'developmentKeyPin':pin(dest/'local-development-key.json')}}
    write(dest/'specification.json',spec)
    return spec['provenance']['promptPins']


if __name__=='__main__':
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','RAYON_NUM_THREADS'):
        os.environ[key]='2'
    print(freeze(Path(ROOT)/'.local/word-table'))
