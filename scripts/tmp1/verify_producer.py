"""Verify producer candidate on invented inputs against the frozen Torch reference and receiver gate."""
import argparse
import csv
import importlib.util
import json
import os
import sys
from pathlib import Path

from assemble import REPO, WEEK, pin

def verify(candidate,fixture,results):
    for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):
        os.environ[key]='2'
    os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false')
    import numpy as np
    import torch
    from transformers import AutoTokenizer, AutoModel
    import tokenizers
    assert tokenizers.__version__=='0.22.2'
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    payload = candidate/'payload'
    sys.path.insert(0,str(payload.resolve()))
    import reader
    from tables import contracts
    where = REPO.parent/'SoundingLine/sounding-line/runners/drive/sealed/week7_tmp1_shell.py'
    spec = importlib.util.spec_from_file_location('receiver_gate',where)
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    gate.verify_bundle(payload,json.loads((candidate/'manifest.json').read_bytes()))
    gate.check_tables(results,contracts())
    scores = reader.Readers()
    inputs = ['A small copper bell.','Why would the toy sail away?','The bronze wheel turned slowly. '*145,'']
    # Use the original fast tokenizer configuration, including truncation and special tokens.
    references = {}
    error = {}
    for name,original in [('base',REPO/'.local/readers/models/minilm'),
                          ('worry',REPO/'.local/trigger/export-worry-a/rp-worry-1/encoder')]:
        tokenizer = AutoTokenizer.from_pretrained(original,local_files_only=True)
        model = AutoModel.from_pretrained(original,attn_implementation='eager',local_files_only=True).eval()
        t = tokenizer(inputs,max_length=128,padding=True,truncation=True,return_tensors='pt')
        with torch.inference_mode():
            hidden = model(**t).last_hidden_state
            mask = t.attention_mask.unsqueeze(-1)
            vec = torch.nn.functional.normalize((hidden*mask).sum(1)/mask.sum(1),dim=1).numpy()
        references[name] = vec
        actual = getattr(scores,name).encode(inputs)
        error[name] = float(np.abs(vec-actual).max())
        np.testing.assert_allclose(actual,vec,rtol=0,atol=2e-5)
    from scipy.special import expit
    b,v = references['base'],references['worry']
    h = scores.channel
    p = h['parameters']
    nine = np.tile(h['constants'],(len(b),1))
    nine[:,h['active']] = expit(b.astype(float)@p[:-1]+p[-1])
    expected = np.column_stack((expit(b@scores.tags['weights'].T+scores.tags['bias']),b@scores.placebo.T,
                 v@scores.worry_head['weights'].T+scores.worry_head['bias'],nine,expit(b.astype(float)@scores.pride[:-1]+scores.pride[-1])))
    actual = scores.score(inputs)
    error['all49'] = float(np.abs(expected-actual).max())
    np.testing.assert_allclose(actual,expected,rtol=0,atol=2e-5)
    counts = {}
    sizes = {}
    for path in results.glob('*.csv'):
        with path.open() as stream:
            records = list(csv.DictReader(stream))
        counts[path.name] = len(records)
        sizes[path.name] = path.stat().st_size
        assert {r['n'] for r in records} == ({'48'} if path.name in ('traits.csv','contrast.csv','channels.csv') else {'32'})
    assert counts['traits.csv']==40 and counts['channels.csv']==2 and counts['contrast.csv']==1
    assert set(counts)==set(contracts())
    # Compare actual candidate executable with the copy of its canonical registered primitives.
    assert pin(payload/'run.py')==pin(REPO/'scripts/tmp1/run.py')
    return dict(manifest=pin(candidate/'manifest.json'),files=len(json.loads((candidate/'manifest.json').read_bytes())),
                originalReferenceMaxAbs=error,absoluteTolerance=2e-5, rows=counts,bytes=sum(sizes.values()),
                gatePin=pin(where),source='invented text only',imagePlatformTest='receiver pending',
                threads=2,torch=torch.__version__,numpy=np.__version__)

if __name__=='__main__':
    p = argparse.ArgumentParser()
    for name in ('candidate','fixture','results','audit'):
        p.add_argument(name,type=Path)
    args=p.parse_args()
    report=verify(args.candidate,args.fixture,args.results)
    with args.audit.open('x') as stream:
        json.dump(report,stream,indent=2)
    print(json.dumps(report))

