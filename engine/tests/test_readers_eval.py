import numpy as np
import pytest

from tompathy_engine.eval.readers.metrics import channel_gates, classification, from_table
from tompathy_engine.eval.readers.tp12 import conditional, em_counts, em_probabilities, policy_for


@pytest.mark.parametrize('upstream', [None, 'a' * 64])
def test_aggregate_binds_own_receipt_and_preserves_upstream(tmp_path, upstream):
    import json

    from tompathy_engine.eval.readers.reporting import land
    from tompathy_engine.packs.registry import sha256

    job = tmp_path / 'job'
    job.mkdir()
    receipt = {'card': 'TP18-probe', 'status': 'complete', 'productionAdmission': False}
    if upstream is not None:
        receipt['sourceReceiptPin'] = upstream
    for name, value in {
        'receipt.json': receipt, 'complete.json': {},
        'exit-verification.json': dict.fromkeys(
            ('nativeExited', 'releaseMatches', 'sharedLeaseAbsent', 'localLeaseAbsent'), True),
        'plan.json': {'snapshotFiles': {}, 'launcherSha256': 'b' * 64},
    }.items():
        (job / name).write_text(json.dumps(value), encoding='utf8')
    destination = tmp_path / 'readers-attention-probe-2026-11.json'
    result = land(job, destination)
    public = json.loads(destination.read_text(encoding='utf8'))
    assert public['sourceReceiptPin'] == result['sourceReceiptPin'] == sha256(job / 'receipt.json')
    assert public.get('upstreamSourceReceiptPin') == upstream
    assert json.loads((job / 'receipt.json').read_text(encoding='utf8')) == receipt
    assert land(job, destination)['status'] == 'unchanged'
    (job / 'receipt.json').write_text(json.dumps({**receipt, 'words': 10}), encoding='utf8')
    with pytest.raises(ValueError, match='Preserve the previous public result'):
        land(job, destination)


def test_metrics_and_missing_nothing_here_never_pass():
    y = np.array([0,1,2]*12)
    p = np.eye(3)[y]
    result = classification(y, p, np.repeat(np.arange(12), 3), ['fear', 'joy', 'no-emotion'], bootstrap=100)
    assert result['accuracy'] == result['macro_f1'] == 1
    assert result['macro_f1_interval'] == [1,1]
    assert result['false_no_emotion'] == 0
    assert channel_gates(result, {'macro_f1': .4}, {})['B3'] is None
    assert not channel_gates(result, {'macro_f1': .4}, {})['pack_eligible']
    checks = {'theme_free_n': 40, 'theme_free_silent': 36, 'revision_n': 10,
              'revision_silent_rate': .9, 'revision_coverage_complete': True}
    assert channel_gates(result, {'macro_f1': .4}, checks)['pack_eligible']
    assert from_table([[10,0],[5,5]])['accuracy'] == .75
    with pytest.raises(ValueError):
        classification(y, p*.9, np.repeat(np.arange(12),3), ['a','b','c'])


def test_counting_estimand_em_and_policy_withholding():
    table = np.array([[.8,.1,.1],[.2,.7,.1],[.3,.2,.5]])
    truth = np.array([.6,.3,.1])
    estimated = em_counts(1000*(truth@table), table)
    assert estimated == pytest.approx(truth, abs=1e-5)
    assert conditional(estimated, 2) == pytest.approx([2/3, 1/3], abs=1e-5)
    assert conditional([0,0,1], 2) is None
    p = np.eye(3)[[0]*6+[1]*3+[2]]
    assert em_probabilities(p, [1/3]*3) == pytest.approx(truth)
    rows = [{'neutralSource':'corpus','size':size,'mixture':mix,'neutralFraction':frac,
             'estimator':method,'mae':.1 if method=='raw' else .2,'top1':.5,'undefined':0}
            for size in (20,60,200) for mix in ('flat','peaked') for frac in (0,.5,.8)
            for method in ('raw','nnls-alpha-1','nnls-alpha-2','nnls-alpha-4')]
    assert policy_for(rows)['status'] == 'no-policy-qualified'
    for row in rows:
        if row['size']==200 and row['estimator']=='nnls-alpha-2':
            row['mae']=.01
    policy=policy_for(rows)
    assert policy['status']=='complete' and policy['minimum']==200 and policy['prior']==2


def test_finetune_joint_heads_checkpoint_and_cooperative_stop(tmp_path):
    import torch
    from safetensors.torch import load_file, save_file

    from tompathy_engine.eval.readers.finetune import Heads, predict
    torch.set_num_threads(2)
    torch.manual_seed(23)

    class TinyEncoder(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.embedding = torch.nn.Embedding(4, 6)

        def get_sentence_embedding_dimension(self):
            return 6

        def tokenize(self, texts):
            return torch.tensor([int(t) for t in texts])

        def forward(self, values):
            return {'sentence_embedding':self.embedding(values)}

    model = Heads(TinyEncoder(), 3)
    before = model.encoder.embedding.weight.detach().clone()
    optimizer = torch.optim.AdamW(model.parameters(), lr=.01)
    logits, ratings = model(['0','1','2'])
    loss = torch.nn.functional.cross_entropy(logits, torch.tensor([0,1,2])) + .1*(ratings**2).mean()
    loss.backward()
    optimizer.step()
    assert not torch.equal(before, model.encoder.embedding.weight)
    path = tmp_path/'checkpoint.safetensors'
    save_file(model.state_dict(), str(path))
    expected, features = predict(model, ['0','1','2'], lambda:None)
    restored = Heads(TinyEncoder(), 3)
    restored.load_state_dict(load_file(str(path)))
    actual, restored_features = predict(restored, ['0','1','2'], lambda:None)
    assert np.allclose(actual, expected) and np.allclose(features, restored_features)
    assert np.allclose(actual.sum(axis=1), 1)

    def stop():
        raise RuntimeError('stop before inference')
    with pytest.raises(RuntimeError, match='stop before inference'):
        predict(restored, ['0'], stop)


def test_stake_joint_excludes_unknown_cells_and_reports_own_marginals():
    from tompathy_engine.eval.readers.tp11 import stake_score
    result = stake_score([['N1','down','self','already'],['N2','down','other','ahead']],
                         ['any','down','any','already'])
    assert result == {'joint_accuracy':.5,'marginal_chance':.5,'scored_columns':[1,3]}


def test_numeric_motive_head_matches_trusted_model_and_rejects_code(tmp_path):
    import json

    import joblib
    from scipy.special import expit
    from sklearn.linear_model import SGDClassifier
    from sklearn.multiclass import OneVsRestClassifier

    from tompathy_engine.eval.readers.motive_head import NumericHeadUnpickler, convert
    from tompathy_engine.packs.registry import sha256
    rng=np.random.default_rng(4)
    x=rng.normal(size=(40,1024))
    y=rng.integers(0,2,size=(40,4))
    fitted=OneVsRestClassifier(SGDClassifier(loss='log_loss',random_state=4)).fit(x,y)
    path=tmp_path/'model_head.pkl'
    joblib.dump(fitted,path)
    (tmp_path/'intake.json').write_text(json.dumps({'files':{'model_head.pkl':sha256(path)}}),encoding='utf8')
    (tmp_path/'config_setfit.json').write_text(json.dumps({'labels':['ach','aff','pow','null']}),encoding='utf8')
    convert(tmp_path,tmp_path/'converted')
    with np.load(tmp_path/'converted/head.npz',allow_pickle=False) as head:
        assert np.allclose(expit(x@head['weights'].T+head['bias']),fitted.predict_proba(x))
    import io
    import pickle
    class Payload:
        def __reduce__(self):
            return print, ('must never run',)
    with pytest.raises(ValueError,match='Unapproved pickle global'):
        NumericHeadUnpickler('test',io.BytesIO(pickle.dumps(Payload())),True).load()
    bad=tmp_path/'objects.pkl'
    joblib.dump(np.array(['text'],dtype=object),bad)
    with bad.open('rb') as stream, pytest.raises(ValueError,match='nonnumeric pickle array'):
        NumericHeadUnpickler(str(bad),stream,True).load()


def test_attention_future_features_obey_sentence_and_page_boundaries():
    from tompathy_engine.eval.readers.tp18 import augment
    text='One, two. Three four'
    spans=[(0,3),(5,8),(10,15),(16,20)]
    source=[{'text':text,'words':[{'start':a,'end':b,'scores':{'V1':float(i+1),'V0':0.,'V5':.5}}
                               for i,(a,b) in enumerate(spans)]}]
    rows=augment(source)[0]['words']
    assert rows[0]['scores']['previous_nats']==0
    assert rows[0]['scores']['sentence_tail_nats']==3
    assert rows[1]['scores']['after_punctuation']==1
    assert rows[1]['scores']['next_nats']==3
    assert rows[2]['scores']['sentence_tail_nats']==7
    assert rows[3]['scores']['next_nats']==rows[3]['scores']['next2_nats']==0
    assert 'next_nats' not in source[0]['words'][0]['scores']


def test_cause_alignment_and_stable_top_k_hit():
    from tompathy_engine.eval.readers.tp17 import hit_rates, token_spans
    assert token_spans('A "good" plan.', ['A','``','good',"''",'plan','.'])==[(0,1),(2,3),(3,7),(7,8),(9,13),(13,14)]
    with pytest.raises(ValueError):
        token_spans('A hidden good plan.', ['A','good','plan','.'])
    assert hit_rates([.1,.1,.2,0],[1])=={'1':0,'3':1,'5':1}


def test_shared_label_mapping_does_not_relabel_unreleased_or_ambiguous_comments():
    from tompathy_engine.eval.readers.tp13 import cross_score
    labels=['joy','anger','caring']
    y=np.array([[1,0,0],[0,1,0],[1,1,0],[0,0,0],[0,0,1]])
    result=cross_score(y,np.array([[.9,.1],[.1,.9],[.9,.1],[.1,.9],[.1,.9]]),labels,['joy','anger'])
    assert result['n']==2 and result['excluded']==3 and result['accuracy']==1


def test_plan_rule_requires_own_first_person_and_known_future_form():
    from tompathy_engine.eval.readers.rated import plans
    assert plans('I plan to call. They will sleep.')==.5
    assert plans('We are going to rest. I have arranged a meeting.')==1
    assert plans('A will is useful. She intends to leave.')==0


@pytest.mark.parametrize('targets', [1, 2])
@pytest.mark.parametrize('sparse', [False, True])
def test_rated_ridge_keeps_single_and_multiple_target_axes(targets, sparse):
    from scipy.sparse import csr_matrix
    from sklearn.linear_model import Ridge

    from tompathy_engine.eval.readers.rated import ridge_forecast
    x = np.arange(36, dtype=float).reshape(12, 3) / 30
    y = np.column_stack([x[:, 0] * (i+1) for i in range(targets)])
    if sparse:
        x = csr_matrix(x)
    expected = Ridge(alpha=3).fit(x[:8], y[:8]).predict(x[8:])
    actual = ridge_forecast(x[:8], y[:8], x[8:])
    assert actual.shape == (4, targets)
    assert np.allclose(actual, expected.reshape(4, targets))
    with pytest.raises(ValueError, match='explicit target axis'):
        ridge_forecast(x[:8], y[:8, 0], x[8:])


def test_rated_retry_reuses_only_exact_verified_initial_cache(tmp_path, monkeypatch):
    import hashlib
    import importlib.metadata
    import json
    from pathlib import Path

    from tompathy_engine.eval.back_half.reporting import save_json
    from tompathy_engine.eval.readers import encoders, rated
    from tompathy_engine.packs.registry import sha256
    source, models, output = tmp_path/'failed', tmp_path/'models', tmp_path/'retry'
    source.mkdir(); output.mkdir()
    texts = ['one', 'two', 'three']
    receipt = {'card':'TP16','source':{'pin':'data'},'n':3,'writers':3,'protocol':{'folds':5},'status':'running','rows':{}}
    for name, value in {
        'receipt.json':receipt,
        'exit-verification.json':dict.fromkeys(('nativeExited','releaseMatches','sharedLeaseAbsent','localLeaseAbsent'),True),
        'failed.json':{'type':'ValueError','reason':'shape mismatch: scalar prediction','completed':[]},
        'phase.json':{'phase':'writer-fold','fold':0},
    }.items(): save_json(source/name, value)
    relative = 'tompathy_engine/eval/readers/encoders.py'
    frozen = source/'code'/relative
    frozen.parent.mkdir(parents=True)
    frozen.write_bytes(Path(encoders.__file__).read_bytes())
    save_json(source/'plan.json', {'snapshotFiles':{relative:sha256(frozen)}})
    identities = {}
    for name in ('potion','minilm'):
        root = models/name; root.mkdir(parents=True)
        (root/'weights').write_bytes(b'fixture')
        intake = {'files':{'weights':sha256(root/'weights')}}
        save_json(root/'intake.json',intake)
        identity = {**intake,'token_cap':128,'device':'cpu','threads':2,'versions':{
            n:importlib.metadata.version(n) for n in ('torch','transformers','model2vec','sentence-transformers','numpy')}}
        identities[name] = identity
        key = hashlib.sha256(json.dumps({'texts':texts,'encoder':identity,'code':sha256(frozen)},sort_keys=True).encode()).hexdigest()
        cache = source/'embeddings'/name/(key+'.npz'); cache.parent.mkdir(parents=True)
        np.savez(cache,embeddings=np.arange(12,dtype=float).reshape(3,4))
    proof = rated.copy_initial_embeddings(source,output,texts,models,receipt)
    def no_inference(_):
        raise AssertionError('Completed encoding must not repeat')
    monkeypatch.setattr(encoders,'load_encoder',lambda directory,kind:(no_inference,identities[kind]))
    for name in identities:
        matrix, _, timing = encoders.embeddings(texts,models/name,name,output/'embeddings'/name,no_inference)
        assert matrix.shape == (3,4) and timing['cache']
        assert proof['caches'][name]['sha256'] == sha256(next((source/'embeddings'/name).glob('*.npz')))
    with pytest.raises(FileNotFoundError):
        rated.copy_initial_embeddings(source,tmp_path/'changed',list(reversed(texts)),models,receipt)
    (source/'complete.json').write_text('{}')
    with pytest.raises(ValueError,match='initial regression shape failure'):
        rated.copy_initial_embeddings(source,tmp_path/'completed',texts,models,receipt)


@pytest.mark.parametrize('card', ['TP15', 'TP16', 'TP19'])
def test_rated_retry_cannot_reset_original_deadline(tmp_path,card):
    import runpy
    from datetime import UTC, datetime
    from pathlib import Path

    from tompathy_engine.eval.back_half.reporting import save_json
    remaining = runpy.run_path(str(Path(__file__).parents[2]/'scripts/engine-readers-job.py'))['remaining_seconds']
    save_json(tmp_path/'plan.json', {'hours':8})
    save_json(tmp_path/'owner.json', {'at':'2026-11-15T17:42:06+00:00'})
    now = datetime(2026,11,15,18,42,6,tzinfo=UTC)
    assert remaining(8,tmp_path,card,now) == 7*3600
    save_json(tmp_path/'plan.json', {'hours':8,'deadlineAt':'2026-11-16T01:42:06+00:00'})
    assert remaining(8,tmp_path,card,now) == 7*3600
    with pytest.raises(ValueError,match='expired'):
        remaining(8,tmp_path,card,datetime(2026,11,16,2,tzinfo=UTC))


@pytest.mark.parametrize('windows_paths', [False, True])
def test_rated_restart_keeps_completed_forecasts_and_skips_completed_training(tmp_path, monkeypatch, windows_paths):
    import hashlib
    from pathlib import Path

    from sklearn.model_selection import GroupKFold

    from tompathy_engine.eval.back_half.reporting import save_json
    from tompathy_engine.eval.readers import longtext, rated, regression
    from tompathy_engine.packs.registry import sha256
    source, output = tmp_path/'source', tmp_path/'retry'
    source.mkdir(); output.mkdir()
    texts = ['common text repeated words'] * 10
    y = np.arange(10,dtype=float)[:,None]
    writers = np.arange(10).astype(str)
    folds = list(GroupKFold(5).split(texts,groups=writers))
    train, test = folds[0]
    unique = sorted(set(writers[train]),key=lambda w:hashlib.sha256(str(w).encode()).hexdigest())
    fit = np.array([i for i in train if writers[i] not in set(unique[:1])])
    d = source/'fold-0'; (d/'encoder').mkdir(parents=True)
    (d/'encoder/model.safetensors').write_bytes(b'fixture encoder')
    (d/'best.safetensors').write_bytes(b'fixture best')
    epochs = [{'epoch':i,'development_rmse':4.-i} for i in (1,2,3)]
    save_json(d/'epochs.json',epochs)
    np.savez(d/'head.npz',mean=y[fit].mean(axis=0).astype(np.float32),scale=y[fit].std(axis=0).astype(np.float32))
    arrays = {name:np.zeros_like(y) for name in ('constant','bow','potion','minilm','fine_tuned')}
    for a in arrays.values(): a[test] = 99
    np.savez(source/'partial-forecasts.npz',**arrays,completed_folds=np.array([1]))
    code = source/'code/tompathy_engine/eval/readers/regression.py'
    code.parent.mkdir(parents=True); code.write_bytes(Path(regression.__file__).read_bytes())
    owner = {'at':'2026-11-15T18:00:00+00:00','native':{'pid':123,'created_ticks':123456}}
    save_json(source/'owner.json',owner)
    audit = {'nativeExited':True,'ownedPythonLaunchers':[],'foreignChanges':False,'ownerNative':owner['native'],
        'hostBootAt':'2026-11-15T19:00:00+00:00','lastHeartbeat':{'at':'2026-11-15T18:30:00+00:00'},
        'phase':{'phase':'writer-fold','fold':1},
        'preservedFiles':{p.relative_to(source).as_posix().replace('/', '\\' if windows_paths else '/'):sha256(p)
            for p in source.rglob('*') if p.is_file()}}
    save_json(source/'host-restart-recovery.json',audit)
    monkeypatch.setattr(rated,'inputs',lambda *_:(texts,y,writers,['worry'],{'test':True}))
    monkeypatch.setattr(rated,'copy_initial_embeddings',lambda *_:{'kind':'host-restart-continuation'})
    monkeypatch.setattr(rated,'embeddings',lambda *_:(np.arange(20).reshape(10,2),{},{}))
    monkeypatch.setattr(longtext,'worry_checks',lambda *_:({'blocked':'policy'},{}))
    calls = []
    def fit_encoder(directory, texts, y, train, test, writers, output, check):
        calls.append(output.name)
        return y[test],{'test':len(test)},lambda _:None
    monkeypatch.setattr(rated,'fit_encoder',fit_encoder)
    monkeypatch.setattr(rated,'scores',lambda *args:{'targets':{'worry':{'r2':0.0}}})
    rated.run('TP16',tmp_path,tmp_path,output,lambda:None,resume=source)
    assert calls == ['fold-1','fold-2','fold-3','fold-4']
    with np.load(output/'forecasts.npz',allow_pickle=False) as saved:
        assert np.array_equal(saved['fine_tuned'][test], arrays['fine_tuned'][test])
        assert np.array_equal(saved['fine_tuned'][np.setdiff1d(np.arange(10),test)],y[np.setdiff1d(np.arange(10),test)])
    assert sha256(d/'best.safetensors') == sha256(output/'fold-0/best.safetensors')
    (d/'best.safetensors').write_bytes(b'changed')
    with pytest.raises(ValueError,match='Preserved restart artifact changed'):
        rated.verified_host_restart(source)


def test_negotiation_prefix_excludes_terminal_and_private_material():
    from tompathy_engine.eval.readers.tp20 import examples, rank_scores
    priority={'High':'Food','Medium':'Water','Low':'Firewood'}
    d={'dialogue_id':7,'participant_info':{p:{'value2issue':priority,'value2reason':'never read'} for p in ('mturk_agent_1','mturk_agent_2')},
       'chat_logs':[{'id':'mturk_agent_1','text':str(i),'task_data':{}} for i in range(6)]+
                   [{'id':'mturk_agent_2','text':'private allocation','task_data':{'data':1}}]}
    rows,excluded=examples([d])
    assert excluded==1 and rows[0]['messages']==['0','1','2','3','4']
    truth=np.array([[3,2,1],[1,2,3]])
    result=rank_scores(truth,truth,np.array(['a','b']))
    assert result['exact_order_accuracy']==1 and result['interval']==[1,1]


def test_choice_history_waits_for_resolution_and_excludes_current_pick():
    from tompathy_engine.eval.readers.tp19 import earlier_preferences
    def row(key,opened,resolved,taken):
        return {'key':key,'writer':'w','open_at':f'2026-01-01T00:00:{opened:02}+00:00',
                'resolved_at':f'2026-01-01T00:00:{resolved:02}+00:00','taken':taken}
    rows=[row('a',0,5,0),row('b',5,8,1),row('c',6,9,0)]
    x={r['key']:np.array([[2.],[0.]]) for r in rows}
    value=earlier_preferences(rows,x)
    assert value['a'][0]==value['b'][0]==0
    assert value['c'][0]==pytest.approx(2/11)
    rows[-1]['taken']=1
    assert earlier_preferences(rows,x)['c'][0]==value['c'][0]


def test_missing_own_option_never_runs_or_invents_reader_features():
    from tompathy_engine.features.augment import reader_option_features
    def fail(*_):
        raise AssertionError('No own-option text exists to read')
    assert reader_option_features(None,fail,readable=[],check=fail)=={'reader_missing':1.}


def test_conditional_choice_is_normalized_and_recovers_constructed_signal():
    from tompathy_engine.eval.readers.tp19 import conditional_forecasts
    rng=np.random.default_rng(23)
    x=rng.normal(size=(50,5,2));y=x[:,:,0].argmax(axis=1)
    p=conditional_forecasts(x,y,np.repeat(np.arange(10),5),lambda:None)
    assert np.allclose(p.sum(axis=1),1)
    assert (p.argmax(axis=1)==y).mean()>.8


def test_longitudinal_estimator_qualifies_and_refuses_zero_variance():
    from tompathy_engine.eval.readers.tp22 import qualify, stability
    assert qualify()['passed']
    with np.errstate(invalid='ignore',divide='ignore'):
        result=stability(np.zeros((25,2,2,1)),['fear'],draws=10)['fear']
    assert not result['variance_measurable'] and not result['stable_above_half']
    assert result['corrected_stability'] is None and result['stability_interval'] is None


def test_blog_reader_orders_dates_and_preserves_missing_date_exclusions():
    from tompathy_engine.eval.readers.tp22 import posts
    text='word '*100
    raw=f'<post>{text}</post><date>02,February,2004</date><post>{text}</post><date>01,January,2004</date><post>{text}</post>'
    rows,excluded=posts(raw)
    assert excluded==1 and [r['date'] for r in rows]==['2004-01-01','2004-02-02']


def test_handling_extensions_do_not_change_the_original_zero_feature_path():
    from tompathy_engine.eval.harness import handling_prequential
    records=[]
    for i in range(4):
        records.append({'key':str(i),'writer':'w','session':'s','prompt':'p','document':'context',
            'menu':['alpha','beta','gamma','delta','epsilon'],'handling':['accept','dismiss','edit','ignore'][i],
            'decision_index':i,'open_at':f'2026-01-01T00:00:{2*i:02}+00:00',
            'resolved_at':f'2026-01-01T00:00:{2*i+1:02}+00:00'})
    base,_=handling_prequential(records)
    extra,_=handling_prequential(records,additional_features={r['key']:[0.,0.] for r in records})
    assert np.allclose([r['probabilities'] for r in base],[r['probabilities'] for r in extra])
    records[-1]['handling']='accept'
    changed,_=handling_prequential(records,additional_features={r['key']:[0.,0.] for r in records})
    assert np.allclose([r['probabilities'] for r in extra],[r['probabilities'] for r in changed])


def test_motive_config_retains_published_labels_without_inverse(tmp_path):
    import json

    from tompathy_engine.eval.readers.tp14 import motive_config
    path=tmp_path/'config.json'
    value={'model_type':'roberta','label2id':{'No':0,'Yes':1},'problem_type':'single_label_classification'}
    path.write_text(json.dumps(value),encoding='utf8')
    config=motive_config(tmp_path)
    assert config.label2id=={'No':0,'Yes':1}
    assert config.id2label=={0:'No',1:'Yes'}
    assert config.num_labels==2 and json.loads(path.read_text())==value
    value['id2label']={'0':'Yes','1':'No'}
    path.write_text(json.dumps(value),encoding='utf8')
    with pytest.raises(ValueError,match='labels differ'):
        motive_config(tmp_path)


@pytest.mark.parametrize('stop_after',[300,None])
def test_motive_checkpoints_survive_the_150_text_timing_boundary(tmp_path,monkeypatch,stop_after):
    from tompathy_engine.eval.readers import tp14

    scored=[]
    texts=[str(i) for i in range(320)]

    def score(batch):
        scored.extend(batch)
        return np.full((len(batch),1),.25)

    monkeypatch.setattr(tp14,'instrument',lambda *_:(score,{'constructed':True}))

    def check():
        if stop_after is not None and len(scored)>=stop_after:
            raise RuntimeError('Injected resource stop')

    if stop_after is not None:
        with pytest.raises(RuntimeError,match='Injected resource stop'):
            tp14.score_instrument(None,'power',None,texts,tmp_path,check)
        assert not (tmp_path/'power-scores.npy').exists()
    else:
        values,_,timing=tp14.score_instrument(None,'power',None,texts,tmp_path,check)
        assert np.all(values==.25) and timing['seconds150']>=0
    saved=np.load(tmp_path/'power-partial.npy',allow_pickle=False)
    covered=np.isfinite(saved).all(axis=1)
    n=int(covered.sum())
    assert len(scored)-63<=n<=len(scored)
    assert covered.tolist()==[True]*n+[False]*(len(texts)-n)
    assert scored==texts[:len(scored)]


def test_cross_corpus_intervals_resample_writers_not_duplicate_rows():
    from tompathy_engine.eval.readers.tp13 import classification
    y=np.array([0,1,0,1,0,1,0,1])
    pred=np.array([0,1,1,0,0,1,1,1])
    writers=np.repeat(['a','b','c','d'],2)
    original=classification(y,pred,writers,label_count=2)
    repeated=classification(np.repeat(y,3),np.repeat(pred,3),np.repeat(writers,3),label_count=2)
    assert original['writers']==repeated['writers']==4
    assert original['accuracy_interval']==repeated['accuracy_interval']
    assert original['macro_f1_interval']==repeated['macro_f1_interval']


def test_regression_intervals_include_variance_bar_and_preserve_undefined():
    from tompathy_engine.eval.readers.regression import scores
    y=np.arange(12,dtype=float)[:,None]
    result=scores(y,y,np.repeat(np.arange(6),2),['worry'],bootstrap=20)['targets']['worry']
    assert result['r2_interval']==[1,1] and result['rmse_interval']==[0,0]
    result=scores(np.ones_like(y),y,np.repeat(np.arange(6),2),['worry'],bootstrap=20)['targets']['worry']
    assert result['r2_interval'] is None and result['undefined_r2_resamples']==20
