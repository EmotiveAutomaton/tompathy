"""File each verified morning readout without repeating model inference."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0,str(Path('engine').resolve()))
from tompathy_engine.eval.evidence import append
from tompathy_engine.eval.readers.reporting import OUTPUTS, land
from tompathy_engine.eval.readers.word_panel_sheets import write_sheet
from tompathy_engine.packs.registry import sha256


def file(job):
    r=json.loads((job/'receipt.json').read_bytes())
    card=r['card']
    plan=json.loads((job/'plan.json').read_bytes())
    for name,h in plan['snapshotFiles'].items():
        if sha256(job/'code'/name)!=h:raise ValueError('Frozen implementation differs')
    for name,h in plan['auxiliaryInputs'].items():
        if sha256(job/name)!=h:raise ValueError('Frozen protocol differs')
    out=Path('engine/validation')/OUTPUTS[card]
    result=land(job,out)
    src=sha256(job/'receipt.json')
    if result['sourceReceiptPin']!=src:raise ValueError('Source receipt mismatch')
    folder=Path('docs/exchange/result-sheets')
    if card=='RD2':
        write_sheet(out,job,folder,Path('.local/nine-channel/preflight/PREFLIGHT_2026-11-20/dot_table.py'),plot_python='python')
        q='Which readers recover the writers’ standards and social norms ratings?'
        data='350 held-out recalled reports and a sensitivity check on the 348 text-fresh reports.'
        estimate={name:{k:v['panels']['registered350']['difference'] for k,v in m.items()} for name,m in r['rows'].items()}
        interval={name:{k:v['panels']['registered350']['interval'] for k,v in m.items()} for name,m in r['rows'].items()}
        bar='A positive paired interval nominates a slot for separate confirmation.'
        verdict='Both slots keep the trained reader. F3 was previously scored; no independent slot confirmation is available.'
        sheet=folder/'RD2-panel.md'
    elif card=='G2-first-rungs':
        q='Did a larger encoder read the seven writers’ words more accurately?'
        data='We compared saved word predictions from MiniLM and MPNet with the frozen reader on the same sources.'
        estimate={k:v['comparison'] for k,v in r['rungs'].items()}
        interval={'seeds':'All individual seeds shown. These are repeated fits on common reports.'}
        bar='Mean AUC gain at least .02 and CARE AUC at least .70 on all three larger-model seeds.'
        verdict='MPNet missed both thresholds in every seed. MiniLM had one measured seed. ModernBERT is pending.'
        sheet=folder/'G2-first-rungs.md'
        lines=['| Encoder | Seed | Mean AUC | Gain over frozen | CARE AUC |','|---|---:|---:|---:|---:|']
        for k,v in estimate.items():
            for seed,s in v['perSeed'].items():
                lines.append(f"| {k.split('/')[-1]} | {seed} | {s['mean']:.4f} | {s['gain']:+.4f} | {s['care']:.4f} |")
    elif card=='TP24-chat':
        q='How often did the fixed table recover the writer’s assigned word group in chat situations?'
        data='The reader scored 20,052 short situations. We compared its first choice with the writer’s assigned group wherever the seven-group mapping applies.'
        estimate=r['row']
        bar='Descriptive comparison against the recalled-report rate. No pass threshold.'
        verdict=f"{estimate['correct']:,} of {estimate['eligibleWriterWords']:,} eligible situations matched ({estimate['accuracyOnAllEligible']:.1%}), versus {estimate['recalledFiveWordAccuracy']:.1%} on recalled reports."
        interval={'definition':'Fixed prefix census. Rates use the full eligible denominator.'}
        sheet=folder/'TP24-chat.md'
        lines=['| Writer group | Eligible | Correct | Table emits group |','|---|---:|---:|---|']
        for k,v in estimate['byChannel'].items():
            lines.append(f"| {k} | {v['eligible']} | {v['correct']} | {v['tableEmitsChannel']} |")
    else:
        q,data,estimate,interval,bar,verdict,lines=[r[k] for k in ('question','data','estimate','interval','bar','verdict','table')]
        sheet=folder/(card+'.md')
    if card in {'G2-first-rungs','TP24-chat','TP34-BK','TP39','TP40','TP39-change'}:
        picture=sheet.with_suffix('.png')
        subprocess.run(['python',str(Path(__file__).with_name('person_teacher_figure.py')),str(out),str(picture)],check=True)
        lines.extend(['',f'![Comparison of the saved estimates]({picture.name})'])
        if card=='TP34-BK':
            lines.extend(['','The word-level precision mean weights each word by the inverse variance approximated from its writer interval width. Writers contribute to several words. The all-situations row directly counts every situation.'])
    if card!='RD2':
        sheet.write_text('\n'.join(['# '+q,'',data,'',verdict,'',*lines,'',bar,'',r['scope'],'',
                          f"[Aggregate {r['ledger']}](../../../engine/validation/{out.name})",'']),encoding='utf8')
    append('engine/validation/EVIDENCE_LEDGER.jsonl',{'id':r['ledger'],'date':'2026-11-21','question':q,'data':data,
           'estimate':{'sourceReceiptPin':src,'result':estimate},'interval':interval,'bar':bar,'verdict':verdict,
           'limit':r['scope'],'claims':{'RD2':['M1','M4'],'G2-first-rungs':['M1'],'TP24-chat':['A1','T1','T2','T3','T4','T5'],'TP33-BK':['S1'],'TP34-BK':['W1'],'TP39':['P3','P2'],'TP39-change':['P3','P2'],'TP40':['M2']}.get(card,[]),
           'family':card+' registered evaluation'})
    print(card,src,verdict)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('jobs',nargs='+',type=Path)
    for job in parser.parse_args().jobs:file(job)
