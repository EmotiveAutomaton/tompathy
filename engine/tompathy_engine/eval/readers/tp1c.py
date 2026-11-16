"""Small-reader conversion and the unchanged five weight-only gates, research only."""
import ctypes
import gc
import importlib.metadata
import json
import runpy
import shutil
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from time import monotonic

from ...ledger.ids import digest
from ...packs.registry import sha256
from ...preview.readers import LocalReader
from ...preview.surface import WORD
from ..back_half.attention import binding_parity, word_forecast
from ..back_half.metrics import paired_auc
from ..back_half.reporting import save_json
from ..two_day.attention import score_resumable
from ..two_day.weightonly import WeightOnlyReader
from ..two_day.weightonly import run as gates


class Smol135Q8(WeightOnlyReader):
    expected_model='HuggingFaceTB/SmolLM2-135M'

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        if int(self.model.metadata['general.file_type'])!=7:
            self.close()
            raise ValueError('TP1c small reader requires Q8_0 conversion')


class Smol360Q4(WeightOnlyReader):
    expected_model='HuggingFaceTB/SmolLM2-360M'
    quantization='Q4_K_M'

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        if int(self.model.metadata['general.file_type'])!=15:
            self.close()
            raise ValueError('TP1c 360M timing requires Q4_K_M conversion')


def converter_copy(source,destination):
    source,destination=Path(source),Path(destination)
    manifest=json.loads((source/'conversion.json').read_text(encoding='utf8'))
    if importlib.metadata.version('llama-cpp-python')!=manifest['wrapperVersion']:
        raise ValueError('Conversion runtime version changed')
    for name,pin in manifest['converterFiles'].items():
        path=(source/name).resolve()
        if not path.is_relative_to(source.resolve()) or sha256(path)!=pin:
            raise ValueError('Pinned converter source differs')
        target=destination/name
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,target)
    return {'sourceReceiptPin':sha256(source/'conversion.json'),'llamaCppCommit':manifest['llamaCppCommit'],
            'wrapper':manifest['wrapperVersion'],'converterFiles':manifest['converterFiles']}


def convert(source,destination,converter,kind,check):
    """In-process conversion belongs to the one counted CPU job."""
    check()
    saved_argv,saved_path=list(sys.argv),list(sys.path)
    sys.path.insert(0,str(converter/'gguf-py'));sys.path.insert(0,str(converter))
    sys.argv=[str(converter/'convert_hf_to_gguf.py'),str(source),'--outfile',str(destination),'--outtype',kind]
    try:
        with destination.with_suffix('.conversion.log').open('w',encoding='utf8') as log,redirect_stdout(log),redirect_stderr(log):
            runpy.run_path(str(converter/'convert_hf_to_gguf.py'),run_name='__main__')
    finally:
        sys.argv=saved_argv
        sys.path=saved_path
    check()
    return sha256(destination)


def run(small,smol,converter,texts_path,intake,output,check):
    small,smol,output=Path(small),Path(smol),Path(output)
    texts=json.loads(Path(texts_path).read_text(encoding='utf8'))
    inputs=json.loads((small/'intake.json').read_text(encoding='utf8'))
    if inputs['id']!='HuggingFaceTB/SmolLM2-135M' or inputs['license_as_read']!='apache-2.0':
        raise ValueError('Wrong small reader intake')
    local=output/'smol135'
    local.mkdir()
    for name,pin in inputs['files'].items():
        path=(small/name).resolve()
        if not path.is_relative_to(small.resolve()) or sha256(path)!=pin:
            raise ValueError('Small reader source differs')
        shutil.copy2(path,local/name)
    save_json(local/'manifest.json',{'model':inputs['id'],'revision':inputs['revision'],'files':inputs['files']})
    conversion=converter_copy(converter,output/'converter')
    report={'card':'TP1c','status':'running','productionAdmission':False,'ledger':'no ledger row',
        'scope':'Smol135 own-reference weight-only gates and exact original TP2 cohort; separate 360M Q4 timing',
        'sourceModelPin':sha256(small/'intake.json'),'converter':conversion,'textPin':sha256(texts_path),
        'pack':'No live route changed; candidate only after all numerical, accuracy and speed criteria',
        'protocol':{'accuracy_target':.5677,'accuracy_tolerance':.005,'speed_target_seconds_per_3000':15,
            'threads':2,'device':'cpu','vocabulary_padding':'Exact assigned vocabulary and output size; no new padding waiver'}}
    save_json(output/'receipt.json',report)
    gguf=output/'smol135-q8.gguf'
    report['ggufPin']=convert(local,gguf,output/'converter','q8_0',check)
    result=gates(local,gguf,texts,output/'gates-a-d.json',check,reader_type=Smol135Q8,allow_unused_padding=False)
    report['gates']=result
    save_json(output/'receipt.json',report)
    if all(result['gates'].get(k,{}).get('passed') for k in 'abcd'):
        source=Path(intake)/'sessions.json'
        sessions=json.loads(source.read_text(encoding='utf8'))
        data_pin=sha256(source)
        check()
        reader=LocalReader(local,threads=2,precision='float32')
        reference,_=score_resumable(sessions,reader,output/'float32',data_pin,{},check)
        del reader;gc.collect();check()
        reader=Smol135Q8(local,gguf,threads=2)
        try:
            candidate,engine=score_resumable(sessions,reader,output/'q8',data_pin,{},check)
        finally:
            reader.close();del reader;gc.collect()
        parity=binding_parity(reference,candidate)
        report['gates']['gates']['e']={**parity,'passed':parity['passes']}
        report['gates']['status']='complete' if parity['passes'] else 'stopped at gate e'
        rows,base=word_forecast(candidate);_,forecast=word_forecast(candidate,['V0'])
        primary=paired_auc([w['stop'] for _,w in rows],base,forecast,[s['writer'] for s,_ in rows])
        report['attention']={**primary,'dataPin':data_pin,'enginePin':engine}
        # This is a candidate comparison, never a substitute for TP2 efficacy.
        accuracy=abs(primary['engine']-.5677)<=.005
        timings=[r for r in result['measurements'] if r['threads']==2]
        long_timings=[r for r in timings if len(list(WORD.finditer(texts[r['text']])))>=3000]
        speed=bool(long_timings) and all(r['secondsPer3000Words']<=15 for r in long_timings)
        report['candidate']=bool(parity['passes'] and accuracy and speed)
        report['criteria']={'accuracy':accuracy,'speed':speed}
        save_json(output/'receipt.json',report)
    # Separately preplanned timing proceeds even if the small-reader gate failed.
    manifest=json.loads((smol/'manifest.json').read_text(encoding='utf8'))
    if manifest['model']!='HuggingFaceTB/SmolLM2-360M' or any(sha256(smol/name)!=pin for name,pin in manifest['files'].items()):
        raise ValueError('Original Smol360 source changed')
    fp16=output/'smol360-f16.gguf'
    convert(smol,fp16,output/'converter','f16',check)
    import llama_cpp
    parameters=llama_cpp.llama_model_quantize_default_params()
    parameters.nthread=2;parameters.ftype=llama_cpp.LLAMA_FTYPE_MOSTLY_Q4_K_M
    target=output/'smol360-q4-k-m.gguf'
    check()
    if llama_cpp.llama_model_quantize(str(fp16).encode(),str(target).encode(),ctypes.byref(parameters))!=0:
        raise RuntimeError('Q4_K_M conversion failed')
    report['q4Pin']=sha256(target)
    check()
    reader=Smol360Q4(smol,target,threads=2)
    timing=[]
    try:
        for name,text in texts.items():
            check();start=monotonic();reader.score(text,check=check)
            elapsed=monotonic()-start
            timing.append({'text':name,'seconds':elapsed,'words':len(list(WORD.finditer(text))),
                'secondsPer3000Words':elapsed*3000/len(list(WORD.finditer(text))),'excludes_loading':True})
        report['q4']={'reader':reader.identity,'measurements':timing,'numericalQualification':'Timing only; no Q4 accuracy or serving admission'}
    finally:
        reader.close()
    report['status']='complete'
    report['aggregatePin']=digest(report.get('gates',{}))
    save_json(output/'receipt.json',report)
