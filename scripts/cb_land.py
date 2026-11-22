"""Land only verified aggregate CB readouts; private source rows stay in the run directories."""
import json
from datetime import UTC, datetime
from pathlib import Path

from cb_inputs import BASE, pin
from cb_features import read


def put(path, data):
    if path.exists():
        if path.read_bytes()!=data:
            raise ValueError('Existing result differs: '+path.name)
        return
    with path.open('xb') as f:
        f.write(data)


def interval(row):
    if row.get('value') is None or None in row.get('interval',[None,None]):
        return 'unavailable'
    a,b=row['interval']
    return f"{row['value']:.3f} [{a:.3f}, {b:.3f}]"


def clear(row):
    lo=row.get('interval',[None,None])[0]
    if lo is None:return None
    return lo>0


def land(card):
    from tompathy_engine.eval.evidence import append
    tasks=['TP44'] if card=='TP44' else ['TP43-all','TP43-read']
    results={};pins={}
    for task in tasks:
        folder=BASE/task
        h=pin(folder/'receipt.json')
        if (read(folder/'complete.json')['sourceReceiptPin']!=h or
            read(folder/'exit-verification.json')['releasePin']!=pin(folder/'released.json')):
            raise ValueError('Missing verified terminal source '+task)
        receipt=read(folder/'receipt.json')
        if receipt['task']!=task or receipt['status']!='complete':
            raise ValueError('Unexpected readout')
        results[task]=receipt['estimate']; pins[task]=h
    if card=='TP44':
        e=results['TP44']
        pleasant=e['table1']['all']['pleasantness']
        repeated=e['table2']['styleCleared']['mean']
        within=e['table1']
        lines=[f"Pleasantness across {pleasant['reports']} reports: {interval(pleasant)}.",
               f"Style-cleared tags across 35 feeling splits: {interval(repeated)}. Uncleared: {interval(e['table2']['uncleared']['mean'])}.",
               f"Country fallback applied in {e['table2']['fallbackCells']} country/city/feeling cells.",
               "Within-feeling pleasantness (each source feeling code, valid reports and 95% interval):",
               *[f"- {k}: {r['pleasantness']['reports']} reports, {interval(r['pleasantness'])}." for k,r in within.items() if k!='all']]
        verdict={'agreement':clear(pleasant),'personAcrossFeelings':clear(repeated)}
        data='7,666 reports available in Table 1. Table 2 uses 1,091 complete respondents; five excluded.'
        limit='One questionnaire sitting, translated reports and limited within-feeling variation.'
    else:
        all_authors=results['TP43-all']['passes']['adjusted']
        feature=results['TP43-read']
        comparisons=[all_authors[k]['table1']['tags'] for k in ('dateHalves','gap')]
        gain=all_authors['table2']['tags']['pairedGain']
        movement=feature.get('table3',{}).get('meanAdjustedCovariance',{})
        supported=[clear(r) for r in comparisons]
        repeat=False if False in supported else True if all(v is True for v in supported) else None
        verdict={'acrossDatesAndGap':repeat,'beyondStyleTopic':clear(gain),'withinWriterMovement':clear(movement)}
        data=f"2,000 selected blog authors; {results['TP43-all']['selectedWithOpenings']} supplied retained openings. Q19 completed texts for {feature['readerB']['wholeAuthorsWithTexts']} whole authors."
        limit='A blog is a public face. Subjects and circumstances can repeat. Topic adjustment captures only 300 words.'
        lines=[f"Adjusted tag stability: date halves {interval(comparisons[0])}; gap {interval(comparisons[1])}.",
               f"Adjusted top-ten gain from adding Tags: {interval(gain)}.",
               f"Adjusted tag covariance for pleasant versus unpleasant posts: {interval(movement)}.",
               feature.get('featureAdjustment',{}).get('status','No whole-author feature pass')+'.']
        if feature['readerB']['wholeAuthorsWithTexts']:
            lines.append('Raw B features are reported separately.')
            if feature.get('limit'):
                lines.append(feature['limit'])
    h=pins[tasks[-1]]
    name='readers-'+card.lower()+'-2026-11.json'
    ledger='E-TP43-20261122' if card=='TP43' else 'no ledger row'
    payload=dict(card=card,status='complete',sourceReceiptPin=h,sourceReceipts=pins,
                 productionAdmission=False,ledger=ledger,estimate=results,verdict=verdict,scope=limit)
    target=Path('engine/validation')/name
    put(target,(json.dumps(payload,ensure_ascii=False,sort_keys=True,allow_nan=False,indent=2)+'\n').encode())
    wording=', '.join(k+' '+('unavailable' if v is None else 'pass' if v else 'miss') for k,v in verdict.items())
    sheet=Path('docs/exchange/result-sheets')/(card+'.md')
    put(sheet,('\n\n'.join(['# '+card,data,'Registered checks: '+wording+'.',*lines,limit,
                             '[Full aggregate and row denominators](../../../engine/validation/'+name+').'])+'\n').encode())
    if card=='TP43':
        append(Path('engine/validation/EVIDENCE_LEDGER.jsonl'),dict(id=ledger,date='2026-11-22',
               question='Do tag levels and contrasts repeat across dates and improve within-corpus matching?',
               data=data,estimate=dict(verdict=verdict,sourceReceiptPins=pins,sourceReceiptPin=h),
               interval='2,000 whole-author draws. Details in aggregate.',bar='Each registered interval above zero.',
               verdict=wording,limit=limit,claims=['P3','P4','P2'],family='TP43 registered evaluation'))
    for path,ref in [('STATUS.md','docs/exchange/'),('docs/ENGINE_SCOREBOARD.md','exchange/'),
                     ('docs/exchange/THEORY_RETURN_2026-11-22.md','')]:
        p=Path(path)
        marker='<!-- CB '+card+' '+h+' -->'
        if marker not in p.read_text(encoding='utf8'):
            with p.open('a',encoding='utf8') as f:
                f.write('\n'+f"**{card}.** {data} {wording}. {lines[0]} {lines[1]} {limit} [Full results]({ref}result-sheets/{card}.md)."+'\n\n'+marker+'\n')
