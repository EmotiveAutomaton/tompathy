"""Writer-held-out twins and proposed stake vocabulary, with frozen encoders."""
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold

from ..back_half.reporting import save_json
from .encoders import embeddings
from .envent import RATINGS, load

PAIRS = [('pride','joy'),('guilt','shame'),('fear','sadness'),('anger','disgust'),('trust','joy')]
EXPECTED = {'ratings':[.613,.627,.728,.749,.798], 'bow':[.757,.700,.863,.787,.891]}
STAKES = {
    'pride':('N4','up','self','already'), 'shame':('N4','down','self','already'),
    'guilt':('N5','down','self','already'), 'trust':('N3','up','other','already'),
    'surprise':('N1','either','any','already'), 'relief':('any','restored','any','already'),
    'fear':('any','threatened','any','ahead'), 'sadness':('any','down','any','already'),
    'anger':('any','down','other','already'), 'disgust':('N6','threatened','any','already'),
    'joy':('any','up','any','already'), 'boredom':('N1','unfed','circumstance','now'),
}


def stake_score(prediction, gold):
    scored = [i for i,value in enumerate(gold) if value not in {'any','either'}]
    matches = np.asarray(prediction)[:,scored] == np.asarray(gold)[scored]
    return {'joint_accuracy':float(matches.all(axis=1).mean()),
            'marginal_chance':float(np.prod(matches.mean(axis=0))), 'scored_columns':scored}


def grouped_auc(y, scores, writers):
    """Uncertainty for pooled out-of-fold predictions, whole writers resampled."""
    unique, inverse = np.unique(writers, return_inverse=True)
    rng = np.random.default_rng(20261115)
    draws=[]
    for _ in range(1000):
        weights=np.bincount(rng.integers(len(unique),size=len(unique)),minlength=len(unique))[inverse]
        if len(np.unique(y[weights>0])) == 2:
            draws.append(roc_auc_score(y,scores,sample_weight=weights))
    return {'pooled_auc':float(roc_auc_score(y,scores)),
            'pooled_interval':np.quantile(draws,[.025,.975]).tolist(),
            'interval_method':'1000 whole-writer resamples of fixed out-of-fold predictions'}


def run(directory, models, output, check):
    output, models = Path(output),Path(models)
    corpus=load(directory)
    frame=corpus.reports
    text=frame.hidden_emo_text.to_numpy()
    ratings=frame[RATINGS].to_numpy(float)
    encoders={}
    identities={}
    for name in ('potion','minilm'):
        encoders[name],identities[name],_=embeddings(text,models/name,name,output/'embeddings'/name,check)
    report={'card':'TP11','status':'running','scope':corpus.summary(),'twins':{},'left_out':{},
        'mapping':{'status':'proposed','source':'November 14 readers packet TP11','table':STAKES},
        'encoderScope':'Original frozen TP10 L2 encoders; no supervised TP10 encoder is used across held-out writers or labels',
        'encoders':identities,'productionAdmission':False,'ledger':'no ledger row'}
    save_json(output/'receipt.json',report)
    for a,b in PAIRS:
        check()
        save_json(output/'phase.json',{'phase':'twins','pair':[a,b]})
        ix=np.flatnonzero(frame.emotion.isin([a,b]))
        y=(frame.iloc[ix].emotion==a).to_numpy(int)
        writers=frame.iloc[ix].prolific_id.to_numpy()
        predictions={name:np.zeros(len(ix)) for name in ('constant','ratings','bow','potion','minilm')}
        folds={name:[] for name in predictions}
        for tr,te in GroupKFold(5).split(ix,y,writers):
            check()
            if set(writers[tr]) & set(writers[te]):
                raise ValueError('Writer leakage')
            predictions['constant'][te]=.5
            folds['constant'].append(.5)
            x=ratings[ix]
            mean,sd=x[tr].mean(axis=0),x[tr].std(axis=0)+1e-9
            inputs={'ratings':((x[tr]-mean)/sd,(x[te]-mean)/sd)}
            vectorizer=TfidfVectorizer(ngram_range=(1,2),min_df=2,sublinear_tf=True)
            inputs['bow']=(vectorizer.fit_transform(text[ix[tr]]),vectorizer.transform(text[ix[te]]))
            inputs.update({name:(x[ix[tr]],x[ix[te]]) for name,x in encoders.items()})
            for name,(train,test) in inputs.items():
                model=LogisticRegression(C=1 if name=='ratings' else 10,max_iter=2000).fit(train,y[tr])
                scores=model.decision_function(test)
                predictions[name][te]=scores
                folds[name].append(float(roc_auc_score(y[te],scores)))
        rows={name:{'mean_fold_auc':float(np.mean(folds[name])),'folds':folds[name],
                    **grouped_auc(y,scores,writers)} for name,scores in predictions.items()}
        # Readers answered 13-way labels on the fixed validation subset. A label
        # outside this binary pair carries no preference and receives score 0.5.
        judgments=corpus.judgments[corpus.judgments.original_emotion.isin([a,b])]
        human_y=(judgments.original_emotion==a).to_numpy(int)
        human_score=np.where(judgments.emotion==a,1.,np.where(judgments.emotion==b,0.,.5))
        human={'auc':float(roc_auc_score(human_y,human_score)), 'judgments':len(judgments),
               'reports':int(judgments.text_id.nunique()),
               'scope':'Five individual reader judgments per fixed validation report; outside-pair votes tied at 0.5. Different subset from model folds.'}
        report['twins'][f'{a}-{b}']={'n':len(ix),'writers':len(np.unique(writers)),'rows':rows,'people':human}
        save_json(output/'receipt.json',report)
    report['twins_gates']={name:all(pair['rows'][name]['mean_fold_auc'] > pair['rows']['ratings']['mean_fold_auc']
        and pair['rows'][name]['mean_fold_auc'] >= pair['rows']['bow']['mean_fold_auc']-.02
        for pair in report['twins'].values()) for name in encoders}
    report['preflight_comparison']={name:{'maximum_absolute_difference':float(max(
        abs(report['twins'][f'{a}-{b}']['rows'][name]['mean_fold_auc']-expected)
        for (a,b),expected in zip(PAIRS,EXPECTED[name])))} for name in EXPECTED}
    # A label is held out from every supervised head and so are its writers.
    for held in ('pride','shame','sadness','anger','joy'):
        check()
        save_json(output/'phase.json',{'phase':'left-out','label':held})
        test=np.flatnonzero(frame.emotion==held)
        excluded_writers=set(frame.iloc[test].prolific_id)
        train=np.flatnonzero(frame.emotion.isin(STAKES) & ~frame.emotion.eq(held)
                            & ~frame.prolific_id.isin(excluded_writers))
        if not len(train):
            raise ValueError('No training rows after strict label/writer holdout')
        rows={}
        target=np.array([STAKES[label] for label in frame.iloc[train].emotion])
        mean=ratings[train].mean(axis=0)
        true_rows=np.array([ratings[frame.emotion.to_numpy()==label].mean(axis=0)-mean for label in corpus.labels])
        for name,x in encoders.items():
            prediction=[]
            for column in range(4):
                head=LogisticRegression(C=10,max_iter=2000).fit(x[train],target[:,column])
                prediction.append(head.predict(x[test]))
            joint=stake_score(np.stack(prediction,axis=1),STAKES[held])
            rated=Ridge(alpha=3).fit(x[train],ratings[train]).predict(x[test])
            predicted_row=rated.mean(axis=0)-mean
            similarities=np.array([np.corrcoef(predicted_row,row)[0,1] for row in true_rows])
            held_index=corpus.labels.index(held)
            rank=int(np.flatnonzero(np.argsort(-similarities)==held_index)[0])+1
            rows[name]={**joint,'ratings_profile_correlation':float(similarities[held_index]),
                        'ratings_own_profile_rank':rank,
                        'ratings_reference':'All-label observed mean rows used only as evaluation templates, never fitted targets for held label'}
        report['left_out'][held]={'n':len(test),'writers':len(excluded_writers),'training':len(train),
                                 'gold_proposal':STAKES[held],'rows':rows}
        save_json(output/'receipt.json',report)
    report['status']='complete'
    report['interpretation']='Joint proposed-column accuracy and 21-feature profile correlation/rank are distinct estimands; no claim that one numerically dominates the other'
    report['pack']='No independent stake answer key; proposed mappings only, no admitted need pack'
    save_json(output/'receipt.json',report)
    return report
