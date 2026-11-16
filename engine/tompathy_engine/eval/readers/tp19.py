"""Observed alternatives, nested writer-held-out choice and exact handling forecasts."""
import json
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp, softmax
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import GroupKFold

from ...features.augment import reader_option_features
from ...features.deterministic import option_features
from ...ledger.ids import digest
from ...ledger.store import Ledger
from ...packs.registry import sha256
from ..back_half.reporting import save_json
from ..harness import handling_prequential
from ..ledger import handling_records
from .checkpoint import completed, load_head
from .envent import RATINGS, READABLE


def prepare_ledger(config,output,check):
    """Compile only the already-pinned public CoAuthor roster into a fresh ledger."""
    from ...adapters.coauthor import compile_session
    config=json.loads(Path(config).read_text(encoding='utf8'))
    roster_path=Path(config['rawRoster'])
    prior=json.loads(Path('.local/bench/two-day-ex1-intake/intake.json').read_text(encoding='utf8'))
    if sha256(roster_path)!=prior['rawRosterPin']:
        raise ValueError('Public CoAuthor roster changed')
    root=Path(config['rawRoot']).resolve()
    roster=json.loads(roster_path.read_text(encoding='utf8'))
    if len(roster)!=1445:
        raise ValueError('CoAuthor source census changed')
    ledger=Ledger(Path(output)/'ledger')
    records=[];proofs=[];exclusions=[];complete=0
    for i,row in enumerate(roster):
        check()
        path=(root/row['path']).resolve()
        if not path.is_relative_to(root/'corpora/coauthor') or sha256(path)!=row['source_sha256']:
            raise ValueError('CoAuthor log source binding differs')
        if not row['reconstructed']:
            exclusions.append({'session':row['session'],'reason':'Original roster reconstruction failed'})
            continue
        events=[json.loads(line) for line in path.read_text(encoding='utf8').splitlines() if line.strip()]
        try:
            added,provenance,omitted=compile_session(events,source_id=row['session'],writer=row['writer'],
                prompt=row['prompt'],source_hash=row['source_sha256'],ledger=ledger)
        except ValueError as exc:
            exclusions.append({'session':row['session'],'reason':str(exc)})
            continue
        records.extend(added);proofs.extend(provenance);complete+=1
        if omitted:
            save_json(Path(output)/'intake-exclusions'/f'{i}.json',omitted)
        if complete%50==0:
            ledger.append_new(records,proofs);records=[];proofs=[]
        save_json(Path(output)/'progress.json',{'intake_sessions':i+1,'total':len(roster),'compiled':complete})
    if records:
        ledger.append_new(records,proofs)
    save_json(Path(output)/'intake.json',{'rosterPin':sha256(roster_path),'sessions':complete,
        'excluded':exclusions,'schema':'Public CoAuthor compiled with the existing observed-decision adapter'})
    if len(exclusions)/len(roster)>.05:
        raise ValueError('More than 5% of source sessions excluded; repair intake before scoring')
    return Path(output)/'ledger'


def bow_forecasts(rows,y,writers,check):
    output=np.zeros((len(rows),5))
    for tr,te in GroupKFold(5).split(rows,y,writers):
        check()
        encoder=TfidfVectorizer(ngram_range=(1,2),min_df=2,sublinear_tf=True,max_features=20000)
        x=encoder.fit_transform([t for i in tr for t in rows[i]['menu']])
        test=encoder.transform([t for i in te for t in rows[i]['menu']])
        truth=y[tr]
        def objective(w,x=x,truth=truth):
            logits=(x@w).reshape(-1,5)
            p=softmax(logits,axis=1)
            loss=np.mean(logsumexp(logits,axis=1)-logits[np.arange(len(truth)),truth])+.005*(w@w)
            p[np.arange(len(truth)),truth]-=1
            return loss,np.asarray(x.T@p.ravel())/len(truth)+.01*w
        fitted=minimize(objective,np.zeros(x.shape[1]),jac=True,method='L-BFGS-B',options={'maxiter':1000})
        if not fitted.success:
            raise ValueError('BOW conditional logit failed: '+str(fitted.message))
        output[te]=softmax((test@fitted.x).reshape(-1,5),axis=1)
    return output


def earlier_preferences(records, vectors, shrink=10):
    """Only a resolved earlier pick can contribute, including across sessions."""
    histories={}
    output={}
    ordered=sorted(records,key=lambda r:(r['open_at'],r['key']))
    for row in ordered:
        opened=datetime.fromisoformat(row['open_at'])
        history=[v for resolved,v in histories.get(row['writer'],[]) if resolved<opened]
        width=vectors[row['key']].shape[1]
        output[row['key']]=sum(history,np.zeros(width))/(len(history)+shrink)
        taken=row.get('taken')
        if taken is not None:
            x=vectors[row['key']]
            delta=x[taken]-np.delete(x,taken,axis=0).mean(axis=0)
            histories.setdefault(row['writer'],[]).append((datetime.fromisoformat(row['resolved_at']),delta))
    return output


def conditional_forecasts(x,y,writers,check):
    x,y=np.asarray(x,float),np.asarray(y,int)
    if x.ndim!=3 or x.shape[1]!=5 or not np.isfinite(x).all():
        raise ValueError('Conditional choice requires exactly five finite offered alternatives')
    result=np.zeros(x.shape[:2])
    for tr,te in GroupKFold(5).split(x,y,writers):
        check()
        # Fold-local scales; a common per-request intercept cancels from utility.
        scale=x[tr].reshape(-1,x.shape[2]).std(axis=0)
        scale[scale<1e-9]=1
        train=x[tr]/scale
        def objective(w,train=train,tr=tr):
            logits=train@w
            p=softmax(logits,axis=1)
            loss=np.mean(logsumexp(logits,axis=1)-logits[np.arange(len(tr)),y[tr]])+.005*(w@w)
            p[np.arange(len(tr)),y[tr]]-=1
            gradient=np.einsum('ij,ijk->k',p,train)/len(tr)+.01*w
            return loss,gradient
        fit=minimize(objective,np.zeros(x.shape[2]),jac=True,method='L-BFGS-B',options={'maxiter':1000})
        if not fit.success:
            raise ValueError('Conditional logit failed to converge: '+str(fit.message))
        result[te]=softmax((x[te]/scale)@fit.x,axis=1)
    return result


def paired_gain(left,right,writers):
    delta=np.asarray(right)-np.asarray(left)
    writers=np.asarray(writers)
    banks=[np.flatnonzero(writers==w) for w in np.unique(writers)]
    rng=np.random.default_rng(23)
    draws=[float(delta[np.concatenate([banks[j] for j in rng.integers(len(banks),size=len(banks))])].mean()) for _ in range(2000)]
    interval=np.quantile(draws,[.025,.975]).tolist()
    return {'gain':float(delta.mean()),'interval':interval,'passed':interval[0]>0,
            'writers':len(banks),'interval_method':'2000 whole-writer resamples of fixed predictions'}


def run(ledger_path,reader_job,output,check,*,motive_job=None,models=None,motive_head=None,source_config=None,resume=None):
    output=Path(output)
    previous=saved=None
    if resume is not None:
        from .tp19_resume import restore
        ledger_path,previous,saved=restore(resume,output,reader_job,ledger_path=ledger_path,motive_job=motive_job,check=check)
    if ledger_path is None:
        if source_config is None:
            raise ValueError('An exact public CoAuthor ledger or source configuration is required')
        ledger_path=prepare_ledger(source_config,output,check)
    ledger=Ledger(ledger_path).snapshot()
    if any(m.source_dataset!='coauthor' for m in ledger.rows('Maker')):
        raise ValueError('This card is authorized only for the public CoAuthor ledger')
    records=handling_records(ledger)
    decisions={d.decision_id:d for d in ledger.rows('Decision')}
    records=[r for r in records if len(r['menu'])==5]
    if not records or len({r['writer'] for r in records})<5:
        raise ValueError('Observed five-option CoAuthor decisions in at least five writers required')
    readable=[RATINGS.index(r) for r in READABLE]
    values,option_rows={},{}
    source=[]
    names=[f'label_{i}' for i in range(13)]+[f'rated_{i}' for i in readable]
    if saved is None:
        _encode,predict,reader=load_head(reader_job)
        # Batch identical strings once, preserving text-based identities, never outcomes.
        texts=sorted({text for r in records for text in r['menu']})
        probabilities,ratings=predict(texts,check)
        numeric=np.c_[probabilities,ratings[:,readable]]
        index={text:i for i,text in enumerate(texts)}
    else:
        reader=saved['reader']
        if saved['names'] != names or set(saved['rows']) != {r['key'] for r in records}:
            raise ValueError('Saved feature names or decision census differ')
    motive=None
    if motive_job is not None:
        completed(motive_job,'TP14')
        from .tp14 import MOTIVES, score_instrument
        # Both instruments stay visible; neither is selected on this outcome.
        scores=[]
        for name in [*MOTIVES,'motive-setfit']:
            z,_identity,_timing=score_instrument(Path(models)/name,name,motive_head,texts,output,check)
            scores.append(z)
        numeric=np.c_[numeric,*scores]
        names += [f'harmony_{m}' for m in MOTIVES]+[f'setfit_{m}' for m in MOTIVES]
        motive={'receiptPin':sha256(Path(motive_job)/'receipt.json'),'instruments':'Both coders, six probabilities; no outcome-based selection'}
    for r in records:
        check()
        d=decisions[r['key']]
        offered=[o for o in d.options if o.origin=='ai' and o.content_ref]
        if len(offered)!=5:
            raise ValueError('Ledger and handling menu differ')
        r['taken']=next((i for i,o in enumerate(offered) if o.option_id==d.taken),None)
        if saved is None:
            values[r['key']]=numeric[[index[t] for t in r['menu']]]
        else:
            rows=saved['rows'][r['key']]
            if set(rows) != {o.option_id for o in d.options}:
                raise ValueError('Saved feature option identities differ')
            values[r['key']]=np.array([[rows[o.option_id][n] for n in names] for o in offered])
            if not np.isfinite(values[r['key']]).all():
                raise ValueError('Nonfinite preserved option features')
        option_rows[r['key']]={o.option_id:dict(zip(names,values[r['key']][i].tolist()))|{'reader_missing':0.}
                              for i,o in enumerate(offered)}
        for o in d.options:
            if o.origin=='maker' and o.content_ref is None:
                option_rows[r['key']][o.option_id]=({'reader_missing':1.} if saved is not None else
                    reader_option_features(None,predict,readable=readable,check=check))
        source.append(d.model_dump(mode='json'))
    if saved is None:
        save_json(output/'option-features.json',{'reader':reader,'motive':motive,'names':names,'rows':option_rows})
    elif saved['rows'] != option_rows:
        raise ValueError('Preserved feature values or missing-option flags differ')
    preference=earlier_preferences(records,values)
    chosen=[r for r in records if r['taken'] is not None]
    y=np.array([r['taken'] for r in chosen]);writers=np.array([r['writer'] for r in chosen])
    base=np.array([[list(option_features(t,r['document'],i).values()) for i,t in enumerate(r['menu'])] for r in chosen])
    current=np.array([values[r['key']] for r in chosen])
    alignment=np.array([values[r['key']]*preference[r['key']] for r in chosen])
    matrices=[base,np.concatenate([base,current],axis=2),np.concatenate([base,current,alignment],axis=2)]
    report={'card':'TP19','status':'running','productionAdmission':False,'ledger':'no ledger row',
        'scope':'Observed CoAuthor five-suggestion choices; no values or endorsement inference',
        'reader':reader,'motives':motive,'sourcePin':digest(source),
        'protocol':{'choice':'GroupKFold(5) by writer, conditional logit L2 .005, scale within training fold',
            'history':'Taken minus mean not-taken, only strictly earlier resolved picks, sum/(n+10); elementwise match with each current option',
            'handling':'Existing exact prequential MAP; added mean and largest reader feature over five options, then mean/largest historical match',
            'primary_metrics':'Choice accuracy and handling negative log loss; positive nested gain excludes zero',
            'own_option':'Missing flag only, no invented continuation text or reader features'},
        'rows':{},'gains':{},'pack':'No automatic about_maker admission; existing admission chain remains required'}
    if previous is not None:
        if any(previous.get(k)!=v for k,v in report.items() if k not in {'rows','gains'}):
            raise ValueError('TP19 continuation source/protocol differs')
        report=previous
    save_json(output/'receipt.json',report)
    correctness=[]
    for stage,x in enumerate(matrices):
        reused=str(stage) in report['rows']
        p=(np.load(output/f'choice-{stage}.npy',allow_pickle=False) if reused else
           conditional_forecasts(x,y,writers,check))
        correct=(p.argmax(axis=1)==y).astype(float);correctness.append(correct)
        row={'choice_accuracy':float(correct.mean()),'choice_log_loss':float(-np.log(p[np.arange(len(y)),y]).mean()),'choices':len(y)}
        if reused:
            if any(report['rows'][str(stage)].get(k)!=v for k,v in row.items()):
                raise ValueError('Preserved choice forecasts do not match their result')
        else:
            report['rows'][str(stage)]=row
            np.save(output/f'choice-{stage}.npy',p)
            save_json(output/'receipt.json',report)
    for stage in (1,2):
        key=f'choice_{stage}_over_{stage-1}'
        if key not in report['gains']:
            if previous is not None:
                raise ValueError('Completed choice gate missing from continuation')
            report['gains'][key]=paired_gain(correctness[stage-1],correctness[stage],writers)
    losses=[]
    for stage in range(3):
        if 'handling' in report['rows'][str(stage)]:
            predictions=json.loads((output/f'handling-{stage}.json').read_text(encoding='utf8'))
            evaluated=[r for r in predictions if r['module']=='backbone']
            expected=sorted(records,key=lambda r:(r['open_at'],r['key']))
            if (len(predictions)!=2*len(expected) or [r['decision'] for r in evaluated]!=[r['key'] for r in expected]
                    or [r['maker'] for r in evaluated]!=[r['writer'] for r in expected]):
                raise ValueError('Preserved handling census differs')
            loss=np.array([r['log_loss'] for r in evaluated])
            if not np.isfinite(loss).all() or float(loss.mean())!=report['rows'][str(stage)]['handling']['mean_log_loss']:
                raise ValueError('Preserved handling losses differ')
            losses.append(loss)
            continue
        save_json(output/'phase.json',{'phase':'handling','stage':stage})
        extra=None
        if stage:
            extra={r['key']:np.r_[values[r['key']].mean(axis=0),values[r['key']].max(axis=0)] for r in records}
        if stage==2:
            extra={r['key']:np.r_[extra[r['key']],(values[r['key']]*preference[r['key']]).mean(axis=0),
                                 (values[r['key']]*preference[r['key']]).max(axis=0)] for r in records}
        def cancel():
            check()
            return False
        predictions,meta=handling_prequential(records,additional_features=extra,cancel=cancel,population_extra_iterations=2000,
            progress=lambda p,stage=stage:save_json(output/'progress.json',{'handling_stage':stage,**p}))
        save_json(output/f'handling-{stage}.json',predictions)
        evaluated=[r for r in predictions if r['module']=='backbone']
        losses.append(np.array([r['log_loss'] for r in evaluated]))
        report['rows'][str(stage)]['handling']={'mean_log_loss':float(losses[-1].mean()),'metadata':meta}
        if stage:
            report['gains'][f'handling_{stage}_over_{stage-1}']=paired_gain(-losses[stage-1],-losses[stage],[r['maker'] for r in evaluated])
        save_json(output/'receipt.json',report)
    save_json(output/'phase.json',{'phase':'choice-bow-control'})
    bow=bow_forecasts(chosen,y,writers,check)
    np.save(output/'choice-bow.npy',bow)
    report.update(status='complete',controls={'choice_chance':.2,'handling':'Population count baseline retained in each forecast file',
        'bow':{'choice_accuracy':float((bow.argmax(axis=1)==y).mean()),
            'choice_log_loss':float(-np.log(bow[np.arange(len(y)),y]).mean()),
            'protocol':'Writer-held-out conditional logit, word 1-2 grams, min_df2, sublinear TF, maximum20000 training-fold terms'},
        'human':'Observed writer choice is the outcome; no independent human forecast reference'})
    save_json(output/'receipt.json',report)
