"""Fixed coverage and feature-row transfer tests; no inferred maker attributes."""
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.special import expit, softmax
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.multiclass import OneVsRestClassifier

from ...packs.registry import sha256
from ..back_half.reporting import save_json
from .affect_data import ed_situations, go_comments
from .checkpoint import load_head
from .envent import RATINGS, READABLE, load
from .metrics import classification as scored_classification
from .metrics import confusion, from_table
from .regression import correlation

# Exact aliases are fixed before scoring. No broad similarity matching of labels.
ALIASES = {'angry':'anger','afraid':'fear','terrified':'fear','ashamed':'shame',
           'embarrassed':'shame','embarrassment':'shame','sad':'sadness',
           'joyful':'joy','proud':'pride','guilty':'guilt','neutral':'no-emotion'}
CHANNELS = {'curiosity':'C1','anger':'C2','annoyance':'C2','furious':'C2',
    'fear':'C3','nervousness':'C3','afraid':'C3','terrified':'C3','anxious':'C3',
    'desire':'C4','caring':'C5','grief':'C6','sadness':'C6','lonely':'C6','devastated':'C6',
    'amusement':'C7','disgust':'C8','embarrassment':'C9','ashamed':'C9'}


def align_labels(labels, reference):
    return [ALIASES.get(label,label) if ALIASES.get(label,label) in reference else None
            for label in labels]


def transfer_rows(predicted, groups, labels, true_rows):
    """Compare shape, never magnitude; nominated new rows stay gated."""
    means = {name:predicted[groups[:,j].astype(bool)].mean(axis=0)
             for j,name in enumerate(labels) if groups[:,j].any()}
    tests=[]
    for name,row in means.items():
        target=ALIASES.get(name,name)
        if target not in true_rows:
            continue
        similarities={key:correlation(row,value) for key,value in true_rows.items()}
        valid={key:value for key,value in similarities.items() if value is not None}
        nearest=max(valid,key=valid.get) if valid else None
        tests.append({'label':name,'reference':target,'correlation':similarities[target],
                      'nearest':nearest,'same_label_nearest':nearest==target})
    values=[r['correlation'] for r in tests if r['correlation'] is not None]
    median=float(np.median(values)) if values else None
    nearest=float(np.mean([r['same_label_nearest'] for r in tests])) if tests else None
    passed=median is not None and median>=.80 and nearest>=.5
    nominated=['caring','lonely','jealous','grateful','curiosity','desire','amusement']
    return {'shared':tests,'median_correlation':median,'same_label_nearest_fraction':nearest,
            'gate_pass':passed,'features':RATINGS,'readable_features':READABLE,
            'proposed_rows':{n:means[n].tolist() for n in nominated if n in means} if passed else {},
            'withheld':[] if passed else [n for n in nominated if n in means],
            'interpretation':'Analyst proposal; model-read other people\'s text. Shape may transfer; size does not.'}


def classification(y,pred,writers=None,*,label_count=None):
    y,pred=np.asarray(y,int),np.asarray(pred,int)
    k=label_count or int(max(y.max(),pred.max()))+1
    result={'n':len(y),'accuracy':float(accuracy_score(y,pred)),
            'macro_f1':float(f1_score(y,pred,labels=np.arange(k),average='macro',zero_division=0))}
    if writers is not None:
        writers=np.asarray(writers)
        if len(writers)!=len(y):
            raise ValueError('Cross-corpus writer groups differ from scored texts')
        groups=np.unique(writers)
        tables=np.array([confusion(y[writers==w],pred[writers==w],k) for w in groups])
        rng=np.random.default_rng(23)
        draws=[from_table(tables[rng.integers(len(tables),size=len(tables))].sum(axis=0)) for _ in range(1000)]
        result.update(writers=len(groups),interval_method='1000 whole-writer resamples; unknown writers are individual texts',
            accuracy_interval=np.quantile([r['accuracy'] for r in draws],[.025,.975]).tolist(),
            macro_f1_interval=np.quantile([r['macro_f1'] for r in draws],[.025,.975]).tolist())
    return result


def cross_score(y, probability, labels, reference, writers=None):
    mapped=align_labels(labels,reference)
    common=sorted({x for x in mapped if x is not None})
    if y.ndim==2:
        # Multi-label comments with exactly one mapped consensus label only.
        joined=np.column_stack([y[:,[i for i,v in enumerate(mapped) if v==name]].max(axis=1)
                                for name in common])
        mask=joined.sum(axis=1)==1
        target=joined[mask].argmax(axis=1)
    else:
        values=np.array([mapped[int(v)] for v in y],dtype=object)
        mask=np.array([v is not None for v in values])
        target=np.array([common.index(v) for v in values[mask]])
    reduced=probability[mask][:,[reference.index(n) for n in common]]
    return {**classification(target,reduced.argmax(axis=1),None if writers is None else np.asarray(writers)[mask],label_count=len(common)),'shared_labels':common,
            'excluded':int((~mask).sum()),'restriction':'Only shared labels; exactly one mapped label for multilabel comments'}


def project_probabilities(probability,labels,reference):
    mapped=align_labels(labels,reference)
    result=np.zeros((len(probability),len(reference)))
    for i,name in enumerate(mapped):
        if name is not None:
            result[:,reference.index(name)]+=probability[:,i]
    return result


def multilabel_score(y,p,writers):
    predicted=p>=.5
    unique,inverse=np.unique(writers,return_inverse=True)
    components=np.zeros((len(unique),3,y.shape[1]))
    for j,values in enumerate((y&predicted,(1-y)&predicted,y&~predicted)):
        np.add.at(components[:,j],inverse,values)
    rng=np.random.default_rng(23)
    draws=[]
    for _ in range(1000):
        a=components[rng.integers(len(unique),size=len(unique))].sum(axis=0)
        denom=2*a[0]+a[1]+a[2]
        draws.append(np.divide(2*a[0],denom,out=np.zeros_like(denom),where=denom>0).mean())
    return {'n':len(y),'macro_f1':float(f1_score(y,predicted,average='macro',zero_division=0)),
            'micro_f1':float(f1_score(y,predicted,average='micro',zero_division=0)),
            'threshold':.5,'subset_accuracy':float(accuracy_score(y,predicted)),
            'macro_f1_interval':np.quantile(draws,[.025,.975]).tolist(),
            'interval_method':'1000 writer resamples; unknown writers are separate texts','writers':len(unique)}


def run(corpus,ed_root,go_root,reader_job,output,check):
    output=Path(output)
    data=load(corpus)
    ed,ed_pin=ed_situations(ed_root)
    go,go_y,go_labels,go_pin=go_comments(go_root)
    encode,_predict,reader_pin=load_head(reader_job)
    receipt={'card':'TP13','status':'running','scope':'Corpus labels and feature shapes; not maker attributes',
        'productionAdmission':False,'ledger':'no ledger row','reader':reader_pin,
        'data':{'envent':data.summary(),'ed':ed_pin,'go':go_pin},'rows':{},'cross':{},'feature_transfer':{},
        'mapping':{'status':'proposed','channels':CHANNELS},
        'protocol':{'label_head':'Logistic C=10, max_iter=1000; published splits; Go one-vs-rest threshold .5',
          'aliases':ALIASES,'feature_reference':'Predicted and observed means centered by the same fixed TP10 training mean, following preflight pf_d',
          'external_numbers':'ED accuracy .43-.48; Go macro-F1 .46, supplied packet references; protocols differ'},
        'pack':'unpacked research use; no failed TP10 gate is rerun'}
    save=lambda:save_json(output/'receipt.json',receipt)
    save()
    g=data.reports
    center=g.iloc[data.train][RATINGS].mean().to_numpy()
    true_rows={name:g.loc[g.emotion==name,RATINGS].mean().to_numpy()-center for name in data.labels}
    # The source feature head is fixed. All raw Go comments receive features,
    # but only released labels can contribute to a labelled group mean.
    for name,frame,truth,labels in [('ed',ed,None,sorted(ed.label.unique())),('go',go,go_y,go_labels)]:
        check()
        save_json(output/'phase.json',{'phase':name})
        texts=frame.text.tolist()
        x=encode(texts,check)
        # Reuse the exact head algebra over these embeddings, avoiding a second pass.
        seed=json.loads((Path(reader_job)/'receipt.json').read_text(encoding='utf8'))['selected_seed']
        with np.load(Path(reader_job)/f'seed-{seed}/head.npz',allow_pickle=False) as heads:
            features=x@heads['ratings_weights'].T+heads['ratings_bias']
            source_weights,source_bias=heads['weights'].copy(),heads['bias'].copy()
            envent_probability=softmax(x@source_weights.T+source_bias,axis=1)
        np.savez(output/f'{name}-vectors.npz',embeddings=x,features=features)
        train=np.flatnonzero(frame.source_split.to_numpy()=='train')
        test=np.flatnonzero(frame.source_split.to_numpy()=='test')
        known=frame.writer_known.to_numpy() if 'writer_known' in frame else np.ones(len(frame),bool)
        held=np.flatnonzero(frame.source_split.isin(['dev','valid','test']))
        held_writers=set(frame.iloc[held[known[held]]].writer)
        original_train=len(train)
        train=np.array([i for i in train if not known[i] or frame.iloc[i].writer not in held_writers])
        writer_groups=np.array([str(frame.iloc[i].writer) if known[i] else 'unknown-text-'+hashlib.sha256(str(frame.iloc[i].id).encode()).hexdigest() for i in test])
        vectorizer=TfidfVectorizer(ngram_range=(1,2),min_df=2,sublinear_tf=True)
        bow_train=vectorizer.fit_transform([texts[i] for i in train])
        bow_test=vectorizer.transform([texts[i] for i in test])
        if truth is None:
            y=np.array([labels.index(v) for v in frame.label])
            model=LogisticRegression(C=10,max_iter=1000,random_state=23).fit(x[train],y[train])
            groups=np.eye(len(labels),dtype=np.int8)[y]
            p=model.predict_proba(x[test])
            row=scored_classification(y[test],p,writer_groups,labels)
            weights,bias=model.coef_,model.intercept_
            bow_model=LogisticRegression(C=10,max_iter=1000,random_state=23).fit(bow_train,y[train])
            bow_p=bow_model.predict_proba(bow_test)
            constant=np.zeros_like(p);constant[:,np.bincount(y[train]).argmax()]=1
            controls={'constant':scored_classification(y[test],constant,writer_groups,labels),
                      'bow':scored_classification(y[test],bow_p,writer_groups,labels)}
            np.savez(output/'ed-bow-head.npz',weights=bow_model.coef_,bias=bow_model.intercept_,idf=vectorizer.idf_)
            save_json(output/'ed-bow-head.json',{'labels':labels,'vocabulary':vectorizer.vocabulary_,
                      'headPin':sha256(output/'ed-bow-head.npz'),'training':'published training only; held-out writers purged'})
        else:
            y=truth
            model=OneVsRestClassifier(LogisticRegression(C=10,max_iter=1000,random_state=23),n_jobs=1).fit(x[train],y[train])
            p=model.predict_proba(x[test])
            groups=y
            row=multilabel_score(y[test],p,writer_groups)
            weights=np.concatenate([e.coef_ for e in model.estimators_])
            bias=np.concatenate([e.intercept_ for e in model.estimators_])
            bow_model=OneVsRestClassifier(LogisticRegression(C=10,max_iter=1000,random_state=23),n_jobs=1).fit(bow_train,y[train])
            controls={'constant':multilabel_score(y[test],np.tile(y[train].mean(axis=0),(len(test),1)),writer_groups),
                      'bow':multilabel_score(y[test],bow_model.predict_proba(bow_test),writer_groups)}
        np.savez(output/f'{name}-head.npz',weights=weights,bias=bias)
        save_json(output/f'{name}-head.json',{'labels':labels,'reader':reader_pin,
            'headPin':sha256(output/f'{name}-head.npz'),'training_split':'train only',
            'multilabel':truth is not None,'source_pin':ed_pin if name=='ed' else go_pin})
        train_writers=set(frame.iloc[train].writer)
        row.update(train=len(train),purged_training_rows=original_train-len(train),
                   test_reports_with_training_writer=int((frame.iloc[test].writer.isin(train_writers).to_numpy()&known[test]).sum()),
                   writerDisjoint=True,headPin=sha256(output/f'{name}-head.npz'),controls=controls,
                   people='No individual human-reader accuracy reference supplied for this corpus')
        receipt['rows'][name]=row
        receipt['feature_transfer'][name]=transfer_rows(features-center,groups,labels,true_rows)
        # Crowd head -> held-out external corpus, plus external train head ->
        # original held-out Crowd reports. No target-corpus refit or tuning.
        receipt['cross'][f'envent_to_{name}']=cross_score(y[test],envent_probability[test],labels,data.labels,writer_groups)
        in_domain=cross_score(y[test],project_probabilities(p,labels,data.labels),labels,data.labels,writer_groups)
        receipt['cross'][f'envent_to_{name}'].update(in_domain_restricted=in_domain,
            accuracy_difference=receipt['cross'][f'envent_to_{name}']['accuracy']-in_domain['accuracy'])
        source_x=encode(g.iloc[data.test].hidden_emo_text.tolist(),check)
        target_p=expit(source_x@weights.T+bias) if truth is not None else softmax(source_x@weights.T+bias,axis=1)
        external_map=align_labels(labels,data.labels)
        shared=sorted({v for v in external_map if v is not None})
        joined=np.column_stack([target_p[:,[i for i,v in enumerate(external_map) if v==n]].sum(axis=1) for n in shared])
        target=g.iloc[data.test].emotion.to_numpy()
        mask=np.isin(target,shared)
        source_writers=g.iloc[data.test].prolific_id.to_numpy()[mask]
        receipt['cross'][f'{name}_to_envent']={**classification(np.array([shared.index(v) for v in target[mask]]),joined[mask].argmax(axis=1),source_writers,label_count=len(shared)),
            'shared_labels':shared,'excluded':int((~mask).sum()),'aggregation':'Sum exact fixed aliases before restricted argmax'}
        own=softmax(source_x@source_weights.T+source_bias,axis=1)[mask][:,[data.labels.index(v) for v in shared]]
        reference=classification(np.array([shared.index(v) for v in target[mask]]),own.argmax(axis=1),source_writers,label_count=len(shared))
        receipt['cross'][f'{name}_to_envent'].update(in_domain_restricted=reference,
            accuracy_difference=receipt['cross'][f'{name}_to_envent']['accuracy']-reference['accuracy'])
        save()
    receipt['status']='complete'
    save()
