"""Constructed back-half controls. These outcomes never enter the scoreboard."""
import hashlib
import json
from contextlib import contextmanager
from copy import deepcopy
from types import SimpleNamespace

import numpy as np
import pytest

from tompathy_engine.eval.back_half import (
    attention,
    data,
    edits,
    goals,
    metrics,
    reporting,
    resources,
)
from tompathy_engine.eval.back_half.protocol import PROTOCOL_PIN, field_status, receipt
from tompathy_engine.eval.back_half.speed import comparison, prefix_quantization_probe
from tompathy_engine.preview.judgments import goal_call
from tompathy_engine.transcribe.cache import Cache


def test_field_flag_requires_exact_registered_natural_receipt():
    row = {"id":"1","registered":True,"bar":.02,"baseline":.5,"engine":.55,"interval":[.03,.07],"clusters":10}
    value = receipt("attention",status="complete",engine_pin="engine",data_pin="data",rows=[row],evidence="natural-writing")
    assert value["protocol"] == PROTOCOL_PIN
    assert field_status("attention",value,engine_pin="engine",data_pin="data") == "unvalidated"
    assert field_status("attention",value,enabled=True,engine_pin="engine",data_pin="data") == "field-tested"
    for change in ({"evidence":"constructed"},{"protocol":"stale"},{"enginePin":"changed"},{"status":"partial"}):
        assert field_status("attention",value|change,enabled=True,engine_pin="engine",data_pin="data") == "unvalidated"
    for change in ({"interval":[.01,.08]},{"bar":.01},{"registered":False},{"engine":float('nan')}):
        assert field_status("attention",value|{"rows":[row|change]},enabled=True,engine_pin="engine",data_pin="data") == "unvalidated"
    assert field_status("goals",value,enabled=True) == "unvalidated"
    with pytest.raises(ValueError):
        receipt("unknown")


def test_cluster_metric_weights_people_not_word_counts():
    y = [0,1]*20 + [0,1]
    base = [.5]*42
    engine = [0,1]*20 + [1,0]
    result = metrics.paired_auc(y,base,engine,["many"]*40+["few"]*2,draws=100)
    assert result["engine"] == .5 and result["gain"] == 0 and result["clusters"] == 2
    assert metrics.auc([0,1],[.5,.5]) == .5
    assert metrics.auc([1,1],[.2,.3]) is None
    with pytest.raises(ValueError):
        metrics.auc([0,1],[0,float('nan')])
    with pytest.raises(ValueError):
        metrics.paired_auc([0,1],[0,1],[0,1],["a","a"])


def test_logistic_fold_predictions_and_failure_guards():
    x = np.array([[-2.],[-1.],[1.],[2.]]*5)
    y = np.array([0,0,1,1]*5)
    folds = np.repeat(np.arange(5),4)
    predicted = metrics.cross_fit(x,y,folds)[:,1]
    assert np.array_equal(predicted>.5,y)
    model = metrics.fit_logistic(x[:4],y[:4])
    assert model["mean"][0] == 0 and model["scale"][0] > 0
    with pytest.raises(ValueError):
        metrics.predict(model,[[float('nan')]])
    with pytest.raises(ValueError):
        metrics.cross_fit(x,y,[0]*20)
    row = metrics.registered_row("3",y,np.full(20,.5),predicted,np.repeat(np.arange(5),4),"attention")
    assert row["reading"] == "hers"


def test_normalization_unicode_and_alignment_controls():
    assert data.normalize("cafe\u0301\r\nword  ") == "café\nword"
    assert data.utf16_to_codepoint("a😀b",3) == 2
    with pytest.raises(ValueError,match="surrogate"):
        data.utf16_to_codepoint("a😀b",2)
    with pytest.raises(ValueError):
        data.utf16_to_codepoint("a",5)
    labels = [{"start":0,"end":4,"source":"writer","stop":True,"logPause":1.},
              {"start":5,"end":9,"source":"suggestion"}]
    aligned,report = data.align_session("café word",{"words":labels,"textSha256":data.text_hash("café word")})
    assert aligned == labels and report["method"] == "exact-hash"
    aligned,report = data.align_session("café  word",{"words":labels,"textSha256":"changed"})
    assert aligned[1]["start"] == 6 and report["alignedFraction"] == 1
    assert data.align_session("a b",{"words":labels,"textSha256":"changed"})[0] is None
    with pytest.raises(ValueError):
        data.align_session("café word",{"words":[labels[0]],"textSha256":data.text_hash("café word")})


def test_bundle_checks_bytes_and_path_escape(tmp_path):
    (tmp_path/'rows.jsonl').write_text('{"fixture":true}\n',encoding="utf8")
    (tmp_path/'README.md').write_text('Constructed fixture',encoding="utf8")
    manifest = {"schema":"tompathy.bench.bundle.v1","kind":"EX1","rows":1}
    for key,name in (("records","rows.jsonl"),("readme","README.md")):
        manifest[key] = {"path":name,"sha256":hashlib.sha256((tmp_path/name).read_bytes()).hexdigest()}
    path = tmp_path/'manifest.json'
    path.write_text(json.dumps(manifest),encoding="utf8")
    assert data.load_bundle(path,"EX1")[1] == [{"fixture":True}]
    (tmp_path/'rows.jsonl').write_text('{}',encoding="utf8")
    with pytest.raises(ValueError,match="digest"):
        data.load_bundle(path,"EX1")
    manifest['records']['path'] = '../outside.json'
    path.write_text(json.dumps(manifest),encoding="utf8")
    with pytest.raises(ValueError,match="escapes"):
        data.load_bundle(path,"EX1")


def test_replay_fixture_and_five_percent_gate(tmp_path):
    from replay_fixtures import fixtures

    from tompathy_engine.preview.surface import WORD
    events = [e|{"eventTimestamp":i} for i,e in enumerate(fixtures()[0]["lines"])]
    raw = '\n'.join(json.dumps(e) for e in events).encode()
    (tmp_path/'events.jsonl').write_bytes(raw)
    text = data.normalize(fixtures()[0]["event"]["end_document"])
    export = {"session":"fixture","writer":"hashed","fold":0,"genre":"fixture","textSha256":data.text_hash(text),
        "words":[{"start":m.start(),"end":m.end(),"source":"writer","stop":False,"logPause":0.} for m in WORD.finditer(text)]}
    roster = [{"session":"fixture","writer":"hashed","path":"events.jsonl","source_sha256":hashlib.sha256(raw).hexdigest()}]
    sessions,excluded = data.replay_exports([export],roster,tmp_path)
    assert sessions[0]["text"] == text and excluded == []
    bad = deepcopy(export)
    bad["textSha256"] = "wrong"
    bad["words"] = [{"start":0,"end":10000,"source":"prompt"}]
    with pytest.raises(data.ReplayMismatch,match="5%") as mismatch:
        data.replay_exports([bad],roster,tmp_path)
    assert mismatch.value.total == 1 and len(mismatch.value.exclusions) == 1


def test_history_has_no_target_future_or_wrong_genre():
    reader = SimpleNamespace(encode=lambda t:{"input_ids":[ord(c) for c in t]})
    sessions = [{"session":f"{w}-{t}","writer":w,"genre":"one","time":t,"text":(w+str(t))*400} for w in ("a","b") for t in (1,2,3)]
    contexts = data.history_contexts(sessions,reader)
    assert contexts['a-1']['own'] == []
    assert contexts['a-2']['eligible'] and contexts['a-2']['own'] == [ord(c) for c in 'a1'*400]
    assert contexts['a-2']['other'] == [ord(c) for c in 'b1'*400]
    assert contexts == data.history_contexts(sessions,reader)
    sessions[0]['genre'] = 'different'
    assert data.history_contexts(sessions,reader)['a-2']['own'] == [ord(c) for c in 'a1'*400]


def numeric_tables():
    tables = []
    text = "Plain words travel. Strange birds settle. Model words repeat. Human words diverge."
    from tompathy_engine.preview.surface import WORD
    for fold in range(5):
        rows = []
        for i,m in enumerate(WORD.finditer(text)):
            stop = i%2 == 0
            pos,initial,paragraph = attention.positions(text,m.start())
            rows.append({"start":m.start(),"end":m.end(),"text":m.group(),"source":"writer" if i<6 else "suggestion",
                "stop":stop,"eligible":i != 0,"logPause":1.,"position":pos,"sentenceStart":initial,"paragraphStart":paragraph,
                "scores":{"V0":float(stop),"V1":float(stop)+1,"V2":float(stop),"V3":float(stop),"V4":float(stop)+.1,"V6":float(stop)-.1,"V5":float(stop)},
                "historyNats":{"V4":.5,"V6":.7}})
        tables.append({"session":str(fold),"writer":str(fold),"fold":fold,"genre":"fixture","time":fold,"text":text,"words":rows})
    return tables


def test_attention_and_involvement_reuse_scores_with_registered_rows():
    tables = numeric_tables()
    result = attention.attention_report(tables,engine_pin="constructed",data_pin="constructed")
    assert [r["id"] for r in result["rows"]] == ['1','2','3']
    assert result['stopsOutsideOwnSet'] > 0
    assert result['exploratoryWinner'] in {'V1','V2','V3','V5'}
    ai = attention.involvement_report(tables,engine_pin="constructed",data_pin="constructed")
    assert [r['id'] for r in ai['rows']] == ['1','2','3']
    public = reporting.public_receipt(ai)
    assert 'countsByWriterGenre' not in public
    assert public['sentences'] > 0
    tables[0]['words'][0]['source'] = 'prompt'
    assert len(attention.sentence_rows(tables)) == len(attention.sentence_rows(numeric_tables()))-1
    assert attention.binding_parity(tables,deepcopy(tables))['passes']
    for session in tables:
        for word in session['words']:
            if word['source'] != 'writer':
                word.pop('stop',None)
    assert attention.binding_parity(tables,deepcopy(tables))['passes']
    altered = deepcopy(tables)
    altered[0]['fold'] = 2
    with pytest.raises(ValueError,match='identical'):
        attention.binding_parity(tables,altered)


def test_text_reader_never_receives_label_or_timing():
    from tompathy_engine.preview.surface import WORD
    calls = []
    text = 'A plain sentence. Another thought.'
    class Reader:
        entropy = True
        def score(self,value,context='',check=lambda:None):
            calls.append((value,context))
            return [{"start":i,"end":i+1,"nats":1.,"entropy":2.} for i in range(len(value))]
    session = {"session":"one","text":text,"words":[{"start":m.start(),"end":m.end(),"source":"writer","stop":True,"logPause":999.} for m in WORD.finditer(text)]}
    table = attention.score_sessions([session],Reader(),histories=False)
    assert calls == [(text,'')]
    assert all(w['scores']['V5'] == 2 for w in table[0]['words'])
    assert attention.scaled([{"nats":1.,"content":True,"held":False}]) == [0.]


def edit_rows():
    return [{"id":f"{fold}-{label}-{j}","writer":str(fold),"fold":fold,"category":label,"postId":"fixture",
        "before":"a","after":"b","features":{"fixture-feature":k},"x":[k,j/10],"featureSeconds":0.,"engineFeatureSeconds":0.} for fold in range(5) for k,label in enumerate(edits.CATEGORIES) for j in range(3)]


def test_edit_coverage_nested_thresholds_and_cascade():
    rows = edit_rows()
    selected,coverage = edits.eligible_edits(rows,['fixture-feature'])
    assert len(selected) == 75 and coverage['up-to-10000:kept'] == 75
    probability,gates,timings = edits.classifier(rows)
    assert probability.shape == (75,5) and set(gates) == {'0','1','2','3','4'}
    assert edits.sample_edits(rows) == edits.sample_edits(rows)
    assert edits.threshold(np.array([[.9,.1,0,0,0],[0,0,.9,.1,0]]),np.array([2,0])) is None
    assert edits.scores(['clarity'],['unclear'])['twoWayAccuracy'] == 0
    measured = {r['id']:{'raw':'wording','category':'clarity','seconds':10.,'inferenceMeasured':True} for r in rows}
    direct = edits.compare_cascade(rows,probability,{str(f):None for f in range(5)},timings,measured)
    assert not direct['cascadeEligible'] and 'threshold' in direct['reason']
    same = np.array([[1. if edits.CATEGORIES[i] == r['category'] else 0. for i in range(5)] for r in rows])
    result = edits.compare_cascade(rows,same,{str(f):.9 for f in range(5)},timings,measured)
    assert result['cascadeEligible'] and not result['defaultEnabled']
    del rows[0]['featureSeconds']
    assert not edits.compare_cascade(rows,same,{str(f):.9 for f in range(5)},timings,measured)['cascadeEligible']
    with pytest.raises(ValueError):
        edits.eligible_edits(rows,['comment'])


def test_q8_uses_exact_hunk_and_reports_projection():
    calls,projections = [],[]
    class Backend:
        def __init__(self):
            self.metrics = {"calls":0}
        @contextmanager
        def checking(self,check):
            yield
    class Reader:
        backend,pin = Backend(),'fixture'
        def ask(self,question,**kwargs):
            calls.append((question,kwargs))
            self.backend.metrics['calls'] += 1
            return {"answer":"wording"}
    rows = [{'id':str(i),'replacement':'new','replaced':'old'} for i in range(50)]
    result = edits.q8_sample(Reader(),rows,list(range(50)),on_projection=projections.append)
    assert len(result) == 50 and projections[0]['requested'] == 50
    assert calls[0] == ('Q8',{'context':'','text':'new','before':'old','admission_test':True})


def test_goal_removal_ranking_and_cluster_pilot():
    text = 'description: secret\nTitle\nAbstract\nsecret\nBody\nMotivation\nanswer\n'
    abstract,motivation = text.index('Abstract'),text.index('Motivation')
    body = goals.without_answers(text,[{'kind':'abstract','start':abstract,'end':text.index('Body')},{'kind':'motivation','start':motivation,'end':len(text)}])
    assert 'secret' not in body and 'answer' not in body and 'Body' in body
    candidates = [{'id':str(i),'text': 'exact motivation' if i == 0 else 'unrelated distraction'} for i in range(50)]
    assert goals.rank_motivation('exact motivation',candidates,'0')['top1'] == 1
    with pytest.raises(ValueError):
        goals.rank_motivation('x',candidates[:49],'0')
    tasks = [{'id':f'{repo}-{i}','repository':repo} for repo in ('peps','eips') for i in range(30)]
    assert len(goals.pilot_sample(tasks)) == 40
    paired = [{'id':str(i),'author':str(i%2),'readers':{name:{'top1':int(name=='departures'),'reciprocalRank':1. if name=='departures' else .5,'seconds':1.} for name in ('body','departures','cues-only')}} for i in range(4)]
    summary = goals.pilot_summary(paired,draws=20)
    assert summary['differences']['body']['top1']['gain'] == 1
    assert summary['pilot']
    assert summary['readers']['body']['secondsPerCall'] is None


def test_goal_call_cache_key_matches_existing_prepared_request(tmp_path):
    from tompathy_engine.ledger.ids import digest
    schema = {'required':['label','description']}
    payload = {'scope':'local','regions':[{'text':'example'}]}
    key = digest(['preview-goals-lenses-v3','fixture',{},'prompt',schema,payload])
    cache = Cache(tmp_path/'cache.sqlite')
    cache.put(key,{'label':'same','description':'same'})
    backend = SimpleNamespace(model_id='fixture',settings={})
    actual,result = goal_call(backend,cache,[],"",prepared=('prompt',schema,payload))
    assert actual == key and result == cache.get(key)


def test_goal_pilot_inputs_calls_and_git_pins(tmp_path,monkeypatch):
    from tompathy_engine.eval.back_half import goal_pilot
    text = 'Title\nBody words explain evidence.\nMotivation\nSecret answer'
    section = {'kind':'motivation','start':text.index('Motivation'),'contentStart':text.index('Secret'),'end':len(text)}
    class Reader:
        def score(self,text,check=lambda:None):
            return [{'start':i,'end':i+1,'nats':float(i%7+1)} for i in range(len(text))]
    inputs,cues = goals.pilot_inputs(text,[section],'Title',[{'text':'Motivation','level':2,'start':section['start']}],Reader())
    assert all('Secret' not in s for s in inputs.values())
    assert [c['text'] for c in cues] == ['Title']
    class Backend:
        model_id,settings = 'fixture',{}
        @contextmanager
        def checking(self,check):
            check()
            yield
        def complete(self,prompt,schema):
            return {'text':json.dumps({'label':'Secret answer','description':'evidence','support':.5,'cue_match':0.,'cue_ids':[]})}
    task = {'id':'true','author':'fixture','truth':'true','candidates':[{'id':'true','text':'Secret answer'}]+[{'id':str(i),'text':'distractor'} for i in range(49)]}
    completed = []
    result = goals.pilot_document(task,inputs,cues,Backend(),Cache(tmp_path/'calls.sqlite'),on_progress=completed.append)
    assert len(result['readers']) == 3
    assert len(completed) == 3 and len(completed[0]['readers']) == 1
    assert goals.pilot_document(task,inputs,cues,Backend(),Cache(tmp_path/'calls.sqlite'),completed=result) == result
    with pytest.raises(ValueError,match='pin'):
        goals.pilot_document(task,inputs|{'body':'changed'},cues,Backend(),Cache(tmp_path/'calls.sqlite'),completed=result)
    task = {'id':'true','repository':'peps','commit':'a'*40,'path':'pep.rst','sha256':hashlib.sha256(text.encode()).hexdigest(),'sections':[section]}
    monkeypatch.setattr(goal_pilot.subprocess,'run',lambda *a,**k:SimpleNamespace(stdout=text.encode()))
    assert goal_pilot.pinned_document(task,{'peps':tmp_path}) == text
    lookup = {str(i):task|{'id':str(i)} for i in range(50)}
    expanded = goal_pilot.materialize(lookup['0']|{'distractors':[str(i) for i in range(1,50)]},lookup,{'peps':tmp_path})
    assert len(expanded['candidates']) == 50
    with pytest.raises(ValueError):
        goal_pilot.pinned_document(task|{'path':'../outside'}, {'peps':tmp_path})


def test_secondary_selection_is_frozen_and_uses_session_clusters():
    from tompathy_engine.eval.back_half.secondary import secondary_report
    tables = numeric_tables()
    class Reader:
        def score(self,text,check=lambda:None):
            return [{'start':i,'end':i+1,'nats':float(i%7+1)} for i in range(len(text))]
    essays = [{'session':s['session'],'text':s['text'],'words':[w|{'stop80':w['stop'],'stop2s':not w['stop'],'insertedLater':False} for w in s['words']]} for s in tables]
    result = secondary_report(tables,essays,Reader(),'V1')
    assert len(result['rows']) == 4 and result['cluster'] == 'session'
    with pytest.raises(ValueError):
        secondary_report(tables,essays,Reader(),'V4')
    with pytest.raises(ValueError,match='distinct'):
        secondary_report(tables,[essays[0],essays[0]],Reader(),'V1')
    malformed = deepcopy(essays)
    malformed[0]['words'].append(malformed[0]['words'][0])
    with pytest.raises(ValueError,match='unique exact'):
        secondary_report(tables,malformed,Reader(),'V1')


def test_reporting_protocol_and_empty_scoreboard(tmp_path):
    reporting.initialize_receipts(tmp_path)
    reporting.initialize_receipts(tmp_path)
    output = tmp_path/'scoreboard.md'
    reporting.scoreboard(tmp_path,output)
    assert output.read_text(encoding='utf8').count('waiting-for-data') == 4
    protocol = json.loads((tmp_path/'back-half-protocol-2026-11.json').read_text())
    protocol['sha256'] = 'changed'
    reporting.save_json(tmp_path/'back-half-protocol-2026-11.json',protocol)
    with pytest.raises(ValueError,match='frozen'):
        reporting.initialize_receipts(tmp_path)
    reporting.bind_run(tmp_path/'private',{'pin':'a'})
    reporting.bind_run(tmp_path/'private',{'pin':'a'})
    with pytest.raises(ValueError,match='differs'):
        reporting.bind_run(tmp_path/'private',{'pin':'b'})
    with pytest.raises(ValueError,match='Unbound'):
        reporting.bind_run(tmp_path,{'pin':'a'})


def test_resources_and_speed_helpers(monkeypatch):
    monkeypatch.setattr(resources,'headroom',lambda:{'ramGiB':30,'commitGiB':19})
    assert resources.guard()['commitGiB'] == 19
    with pytest.raises(RuntimeError):
        resources.guard(large_model=True)
    with pytest.raises(ValueError):
        resources.benchmark_priority(4)
    text = 'tiny fixture'
    tokens = [{'start':i,'end':i+1,'nats':float(i+1)} for i in range(len(text))]
    assert comparison(text,tokens,tokens)['spearman'] == pytest.approx(1.)
    from test_kv_reader import tiny_reader
    probe = prefix_quantization_probe(tiny_reader(),'tiny fixture '*100)
    assert probe['maxAbsoluteTokenNats'] < .001


def test_failed_int8_kv_is_refused_before_live_model_loading(monkeypatch,capsys,tmp_path):
    import sys

    from tompathy_engine import cli
    monkeypatch.setattr(sys,'argv',['tompathy-engine','serve','--token-file',str(tmp_path/'token'),'--preview-scoring','kv'])
    with pytest.raises(SystemExit):
        cli.main()
    assert 'int8 failed' in capsys.readouterr().err


def test_saved_attention_requires_unchanged_scores(tmp_path,monkeypatch):
    from tompathy_engine.eval.back_half.__main__ import saved_attention
    from tompathy_engine.ledger.ids import digest
    monkeypatch.chdir(tmp_path)
    directory = tmp_path/'.local/bench/fixture'
    tables = numeric_tables()
    pins = {'enginePin':'e','dataPin':'d','wordScoresSha256':digest(tables)}
    reporting.save_json(directory/'scoring-identity.json',pins)
    reporting.save_json(directory/'word-scores.json',tables)
    reporting.save_json(directory/reporting.FILES['attention'],receipt('attention',status='complete',engine_pin='e',data_pin='d'))
    assert saved_attention(directory)[0] == tables
    tables[0]['words'][0]['scores']['V0'] = 999.
    reporting.save_json(directory/'word-scores.json',tables)
    with pytest.raises(ValueError,match='word scores'):
        saved_attention(directory)


def test_large_model_gate_is_rechecked_at_actual_load(monkeypatch):
    from tompathy_engine.preview.fixed_backend import FixedQwen
    monkeypatch.setattr(resources,'headroom',lambda:{'ramGiB':30.,'commitGiB':19.})
    backend = FixedQwen('http://127.0.0.1:19999',before_load=lambda:resources.guard(large_model=True))
    monkeypatch.setattr(backend,'inspect',lambda client:[])
    with pytest.raises(RuntimeError,match='20 GiB'):
        backend.complete('fixture',{'type':'object'})
    assert not backend.owned and not backend.uncertain and backend.metrics['calls'] == 0


def test_pilot_deadline_survives_restart_and_cleanup_failure_retains_results(tmp_path):
    from datetime import UTC, datetime, timedelta

    from tompathy_engine.eval.back_half.state import PilotDeadline, finalize
    start = datetime(2026,11,11,tzinfo=UTC)
    first = PilotDeadline(tmp_path/'deadline.json',now=lambda:start)
    first.check()
    later = PilotDeadline(tmp_path/'deadline.json',now=lambda:start+timedelta(hours=8))
    assert first.state == later.state
    with pytest.raises(RuntimeError,match='does not reset'):
        later.check()
    def failed_cleanup(**kwargs):
        raise RuntimeError('fixture unload failed')
    report = receipt('goals',status='complete pilot') | {'completedDocuments':2}
    with pytest.raises(RuntimeError,match='unload'):
        finalize(report,tmp_path/'receipt.json',SimpleNamespace(close=failed_cleanup))
    saved = json.loads((tmp_path/'receipt.json').read_text())
    assert saved['completedDocuments'] == 2 and saved['status'] == 'cleanup-failed'
    assert saved['productionAdmission'] is False


def test_q8_projection_is_bound_and_short_sample_completes():
    from tompathy_engine.ledger.ids import digest
    rows = [{'id':str(i),'replaced':'old','replacement':str(i)} for i in range(12)]
    indices = list(range(12))
    complete = {str(i):{'readerPin':'r','inferenceMeasured':True,'seconds':2.,'inputPin':digest(['old',str(i)])} for i in indices}
    result = edits.first_call_projection(rows,indices,complete,'r','data')
    assert result['completed'] == 12 and result['requested'] == 12 and result['projectedSeconds'] == 24
    assert edits.sample_pin(rows,indices) != edits.sample_pin(rows,indices[::-1])
    with pytest.raises(ValueError,match='entire initial'):
        edits.first_call_projection(rows,indices,{},'r','data')
    complete['0']['inferenceMeasured'] = False
    assert edits.first_call_projection(rows,indices,complete,'r','data')['projectedSeconds'] is None
    with pytest.raises(ValueError,match='reader'):
        edits.first_call_projection(rows,indices,complete,'other','data')


def test_cli_q8_resource_failure_writes_stopped_receipt(tmp_path,monkeypatch):
    import sys

    from tompathy_engine.eval.back_half import __main__ as commands
    monkeypatch.chdir(tmp_path)
    (tmp_path/'docs').mkdir()
    monkeypatch.setattr(commands,'load_bundle',lambda *args:({'featureNames':['fixture-feature']},edit_rows()))
    monkeypatch.setattr(commands,'benchmark_priority',lambda threads:None)
    def unavailable(**kwargs):
        raise RuntimeError('fixture resource gate')
    monkeypatch.setattr(commands,'guard',unavailable)
    monkeypatch.setattr(sys,'argv',['back-half','edit-q8','--bundle','fixture','--url','http://127.0.0.1:19999'])
    with pytest.raises(RuntimeError,match='resource'):
        commands.main()
    output=json.loads((tmp_path/'engine/validation/edit-reasons-2026-11.json').read_text())
    assert output['status']=='stopped Q8 benchmark' and output['completedCalls']==0
    assert output['feature']['edits']==75 and output['productionAdmission'] is False
    assert (tmp_path/'.local/bench/november-run/failure.json').exists()
