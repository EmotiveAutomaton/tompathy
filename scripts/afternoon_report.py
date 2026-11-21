"""Land a terminal local addendum card with a unique source-bound aggregate and result sheet."""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0,str(Path('engine').resolve()))
from tompathy_engine.eval.evidence import append


def read(p):return json.loads(p.read_bytes())


def pin(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def put(p,raw):
    if p.exists():
        if p.read_bytes()!=raw:raise ValueError('Existing landing differs: '+p.name)
    else:
        with p.open('xb') as f:f.write(raw)


def land(job):
    r=read(job/'receipt.json')
    h=pin(job/'receipt.json'); card=r['card']; e=r['estimate']
    ex=read(job/'exit-verification.json')
    if not (read(job/'complete.json')['receiptPin']==h and all(ex[k] for k in ('nativeExited','releaseMatches','sharedLeaseAbsent','localLeaseAbsent'))):
        raise ValueError('Terminal verification missing')
    for name,digest in read(job/'plan.json')['snapshotFiles'].items():
        if pin(job/'code'/name)!=digest:raise ValueError('Snapshot changed')
    sheet=Path('docs/exchange/result-sheets')/(card+'.md')
    out=Path('engine/validation')/('readers-'+card.lower()+'-2026-11.json')
    if card=='TP42':
        data='We counted writers, texts and distinct dates within each local research release, keeping overlapping sources separate.'
        lines=['| Source | 20+ texts | 2+ dates | Both | Median texts / dates for both |','|---|---:|---:|---:|---|']
        for name,v in e.items():
            if 'unavailable' in v:
                lines.append(f"| {name} | — | — | — | {v['unavailable']} |");continue
            groups=[v[k] for k in ('atLeast20','multipleDates','both')]
            both=groups[-1]; med='—' if not both or not both['authors'] else f"{both['medianTexts']:g} / {both['medianDates']:g}"
            counts=[str(g['authors']) if g is not None else '—' for g in groups]
            lines.append('| '+' | '.join([name,*counts,med])+' |')
        lines+=['','The aggregate includes medians for each qualifying group. A dash means the required field or qualifying group was absent.']
        blog,go=e['Blog Authorship Corpus'],e['GoEmotions']
        headline=(f"The blog corpus has {blog['multipleDates']['authors']:,} authors on multiple dates, including "
                  f"{blog['both']['authors']:,} with at least 20 posts. GoEmotions has {go['multipleDates']['authors']:,} on multiple dates, "
                  "including two with 20 comments. The prediction of fewer than 200 in every source missed.")
    else:
        data=f"We compared pleasant and unpleasant assigned situations in both halves of {e['support']['writers']} writers’ texts."
        lines=['| Reading or set | Adjusted contrast covariance [95% interval] | Level covariance [95% interval] |','|---|---:|---:|']
        def cell(x):return f"{x['value']:.4f} [{x['interval'][0]:.4f}, {x['interval'][1]:.4f}]"
        for name,v in [*e['sets'].items(),*e['readings'].items()]:
            lines.append(f"| {name} | {cell(v['adjusted'])} | {cell(v['level'])} |")
        headline=f"{r['verdict']}. Mean adjusted tag covariance {cell(e['sets']['tags']['adjusted'])}. A quarter of tag level covariance was {e['quarterTagLevel']:.4f}."
    public={k:r[k] for k in ('card','ledger','protocolPin','estimate','interval','bar','verdict','scope','productionAdmission')}
    public.update(sourceReceiptPin=h,data=data)
    put(out,(json.dumps(public,indent=2,allow_nan=False)+'\n').encode())
    original=('\n'.join(['# '+r['question'],'',data,'',headline,'',*lines,'',r['bar'],'',r['scope'],'',
                          f"[Aggregate {r['ledger']}](../../../{out.as_posix()})",''])).encode()
    if card=='TP42':
        extra=['','| Source | Median texts / dates among writers with 20+ texts | Median texts / dates among writers on 2+ dates |',
               '|---|---:|---:|']
        def medians(group):
            if not group or not group['authors']:return '—'
            dates=group['medianDates']
            return f"{group['medianTexts']:g} / "+('unavailable' if dates is None else f'{dates:g}')
        for name,v in e.items():
            if 'atLeast20' in v:extra.append(f"| {name} | {medians(v['atLeast20'])} | {medians(v['multipleDates'])} |")
    else:
        extra=['','![Adjusted contrast estimates in 270 writers](TP41.png)','',
               'Circles show equal-weight means and paired writer intervals. Diamonds weight the individual readings by inverse squared interval width as an approximation to inverse variance.']
    final=original+('\n'.join(extra)+'\n').encode()
    if sheet.exists() and sheet.read_bytes()==original:
        tmp=sheet.with_suffix('.tmp')
        put(tmp,final);tmp.replace(sheet)
    else:put(sheet,final)
    append('engine/validation/EVIDENCE_LEDGER.jsonl',{'id':r['ledger'],'date':'2026-11-21','question':r['question'],'data':data,
           'estimate':{'sourceReceiptPin':h,'result':e},'interval':r['interval'],'bar':r['bar'],'verdict':headline,'limit':r['scope'],
           'claims':['P4'] if card=='TP41' else ['P3'],'family':card+(' afternoon addendum' if card=='TP41' else ' support inventory for TP39 follow-up; no test of P3')})
    print(headline)


if __name__=='__main__':
    land(Path(sys.argv[1]))
