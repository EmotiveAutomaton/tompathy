"""Adapters for received EX1–EX3; no imputed labels or private output in receipts."""
import hashlib
import json
import math
import unicodedata
from collections import Counter
from pathlib import Path

from ...adapters.history import diff_hunks
from ...adapters.replay import replay
from ...ledger.ids import digest
from ...preview.surface import WORD
from ..back_half.reporting import save_json


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf8"))


def verify_export(directory, card):
    directory = Path(directory).resolve()
    manifest = read(directory / "MANIFEST.json")
    if manifest.get("card") != card or not manifest.get("files"):
        raise ValueError("Wrong or unpinned received export")
    for name, expected in manifest["files"].items():
        path = (directory / name).resolve()
        if not path.is_relative_to(directory) or sha(path) != expected:
            raise ValueError("Received export hash/path mismatch")
    return manifest, digest({"manifest":sha(directory/"MANIFEST.json"), "readme":sha(directory/"README.md")})


def join_words(text, exported):
    """No nearest-word label transfer: exact spans or an explicit unknown."""
    previous, lookup = 0, {}
    for row in exported:
        a,b = row["start"],row["end"]
        if type(a) is not int or type(b) is not int or not previous <= a < b <= len(text):
            raise ValueError("Invalid exported word spans")
        if row["source"] not in {"typed","accepted_suggestion","prompt",None}:
            raise ValueError("Unknown EX1 source label")
        stop,pause = row["stop"],row["log_pause"]
        supported = row["timing_status"] == "supported"
        if supported != (type(stop) is bool and type(pause) in (int,float) and math.isfinite(pause)):
            raise ValueError("Timing quality/label disagreement")
        if not supported and (stop is not None or pause is not None):
            raise ValueError("Unsupported timing must remain null")
        if supported and row['source'] != 'typed':
            raise ValueError("Only typed words have timing labels")
        lookup[a,b] = row
        previous = b
    output, counts = [], Counter()
    for match in WORD.finditer(text):
        row = lookup.get(match.span())
        source = {"typed":"writer","accepted_suggestion":"suggestion","prompt":"prompt",None:"unknown"}[row['source']] if row else 'unknown'
        if row and (row['mixed_provenance'] or row['unresolved_provenance']):
            source = 'unknown'
        stop = row['stop'] if row and source == 'writer' else None
        counts['matchedWords' if row else 'unmatchedEngineWords'] += 1
        counts['unsupportedTiming'] += int(source == 'writer' and stop is None)
        counts['unknownSource'] += int(source == 'unknown')
        output.append({'start':match.start(),'end':match.end(),'source':source,'stop':stop,
                       'logPause':row['log_pause'] if stop is not None else None})
    counts['unmatchedExportWords'] = len(lookup)-sum(match.span() in lookup for match in WORD.finditer(text))
    return output,counts


def ex1_sessions(directory, config, output, check=lambda:None):
    directory,output = Path(directory),Path(output)
    manifest, export_pin = verify_export(directory,'EX1')
    if manifest.get('schema') != 'EX1-NFC-1':
        raise ValueError('Unreviewed EX1 schema')
    at = Path(config['ex1Source'])
    if sha(at/'PLAN.json') != manifest['source_pins']['at_plan'] or sha(at/'COMPLETE.json') != manifest['source_pins']['at_complete']:
        raise ValueError('EX1 source plan/completion changed')
    bound = read(at/'PLAN.json')['inputs']
    roster_path = Path(bound['raw_roster'])
    if sha(roster_path) != manifest['source_pins']['raw_roster']:
        raise ValueError('EX1 raw roster changed')
    timing_root = Path(bound['timing_root'])
    if sha(timing_root/'COMPLETE.json') != manifest['source_pins']['timing_root']:
        raise ValueError('EX1 timing source changed')
    timing_file = 'output/PRIVATE_ROSTER.json'
    if sha(timing_root/timing_file) != read(timing_root/'COMPLETE.json')['outputs'][timing_file]:
        raise ValueError('Timing roster is not completion-bound')
    roster_rows,timing_rows = read(roster_path),read(timing_root/timing_file)
    roster = {r['session']:r for r in roster_rows}
    timing = {r['session']:r for r in timing_rows}
    if len(roster) != len(roster_rows) or len(timing) != len(timing_rows):
        raise ValueError('Repeated source session identity')
    root = Path(bound['repo_root']).resolve()
    sessions,excluded,counts,folds,seen = [],[],Counter(),{},set()
    for name in sorted(manifest['files']):
        check()
        if not name.startswith('sessions/'):
            continue
        label = read(directory/name)
        sid,writer,fold = label['session_id'],label['hashed_writer_id'],label['writer_fold']
        if sid in seen or type(fold) is not int or fold not in range(5) or (writer in folds and folds[writer] != fold):
            raise ValueError('Repeated identity or crossing writer fold')
        seen.add(sid); folds[writer] = fold
        source,meta = roster[sid],timing[sid]
        if source['writer'] != writer or meta['writer'] != writer:
            raise ValueError('Writer mapping differs from canonical roster')
        raw_path = (root/source['path']).resolve()
        if not raw_path.is_relative_to(root) or sha(raw_path) != source['source_sha256']:
            raise ValueError('Raw replay source changed')
        events = [json.loads(line) for line in raw_path.read_text(encoding='utf8').splitlines() if line]
        result = replay(events)
        text = unicodedata.normalize('NFC',result['final_document'].replace('\r\n','\n').replace('\r','\n').rstrip()) if result['reconstructed'] else ''
        if not result['reconstructed'] or hashlib.sha256(text.encode()).hexdigest() != label['normalized_text_sha256']:
            excluded.append({'session':sid,'reason':'replay/hash mismatch'})
            continue
        if len(text) != label['normalized_codepoints']:
            raise ValueError('EX1 text length differs')
        times = [float(e['eventTimestamp']) for e in events]
        if not times or not all(math.isfinite(t) for t in times) or times != sorted(times):
            excluded.append({'session':sid,'reason':'nonmonotonic chronology'})
            continue
        words,coverage = join_words(text,label['words'])
        counts.update(coverage)
        sessions.append({'session':sid,'writer':writer,'fold':fold,'genre':meta['genre'],'time':times[0],
                         'text':text,'words':words,'alignment':{'method':'exact-hash/exact-word-span','alignedFraction':coverage['matchedWords']/max(1,len(words))}})
        if len(sessions) % 100 == 0:
            save_json(output/'intake-progress.json',{'sessions':len(sessions),'excluded':len(excluded)})
    if len(seen) != manifest['sessions']:
        raise ValueError('EX1 session count differs')
    save_json(output/'exclusions.json',excluded)
    report = {'exportPin':export_pin,'rawRosterPin':sha(roster_path),'timingRosterPin':sha(timing_root/timing_file),
              'sessions':len(sessions),'totalSessions':len(seen),'writers':len({s['writer'] for s in sessions}),
              'counts':dict(counts),'exclusions':dict(Counter(r['reason'] for r in excluded))}
    save_json(output/'intake.json',report)
    if sum(r['reason']=='replay/hash mismatch' for r in excluded)/max(1,len(seen)) > .05:
        raise ValueError('More than 5% EX1 replay/hash mismatch; scoring refused')
    save_json(output/'sessions.json',sessions)
    return sessions,report


def ex2_edits(directory):
    _,pin = verify_export(directory,'EX2')
    raw = read(Path(directory)/'EDITS.json')
    categories = {'typo_spelling':'typo or spelling','grammar':'grammar','clarity':'clarity',
                  'added_content':'added content','removed_content':'removed content'}
    rows,counts = [],Counter()
    for index,row in enumerate(raw):
        if row['reason_category'] not in categories or row['classifier_output'] not in categories or type(row['user_fold']) is not int or row['user_fold'] not in range(5):
            raise ValueError('Invalid EX2 label/fold')
        band = 'over-10000' if max(len(row['before']),len(row['after'])) > 10000 else 'up-to-10000'
        counts[band+':total'] += 1
        hunks = diff_hunks(row['before'],row['after'])
        if len(hunks) != 1:
            counts[band+':not-single-hunk'] += 1
            continue
        start,end,replacement = hunks[0]
        if max(end-start,len(replacement)) > 12000:
            counts[band+':over-12000-hunk'] += 1
            continue
        counts[band+':kept'] += 1
        rows.append({'id':digest([pin,index]),'fold':row['user_fold'],'postId':row['post_id'],
                     'source':row['attribution_url'],'category':categories[row['reason_category']],
                     'before':row['before'],'after':row['after'],'replaced':row['before'][start:end],
                     'replacement':replacement,'upstreamPrediction':categories[row['classifier_output']]})
    return rows,{'exportPin':pin,'coverage':dict(counts),'missing':['feature vectors','held-out probabilities','feature generation timings','editor identity mapping']}
