"""One authorized F2 transfer, after the Spark has frozen its development choices."""
import argparse
import hashlib
import json
import os
import re
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

REMOTE='/home/agent/tompathy-open/word-table-20261120'
ENV='/home/agent/venvs/engine/bin/python'
FILES=('F2-texts.json','F2-token-lengths.json')


def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def save(path,data):
    temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(data,sort_keys=True,allow_nan=False)+'\n',encoding='utf8')
    os.replace(temp,path)


def status(root):
    out=root/'jobs/Q5'
    if (root/'STOP').exists() or any((out/n).exists() for n in ('failed.json','complete.json','STOP')):
        return {'ready':False,'terminal':True}
    if not (out/'F2-awaiting.json').is_file():
        return {'ready':False,'terminal':False}
    ask=read(out/'F2-awaiting.json')
    selection=out/'development-selection.json'
    entry=read(root/'queue.json')['jobs']['Q5']
    owner=read(out/'owner.json')
    stat=Path('/proc')/str(owner['pid'])/'stat'
    if (not stat.is_file() or stat.read_text().rsplit(') ',1)[1].split()[19]!=owner['startTicks']
            or Path('/proc/sys/kernel/random/boot_id').read_text().strip()!=owner['bootId']):
        return {'ready':False,'terminal':False}
    if (owner['commit']!=entry['commit'] or ask['entryPin']!=entry['sourcePin']
            or ask['selectionPin']!=digest(selection) or set(read(selection)['winners'])!={'standards','social_norms'}):
        raise ValueError('Unverified Q5 development selection')
    return {'ready':True,'terminal':False,**ask}


def accept(root, selection):
    st=status(root)
    if not st.get('ready') or st['selectionPin']!=selection:
        raise ValueError('F2 release boundary has not been reached')
    folder=root/'F2-release'
    pins={n:digest(folder/n) for n in FILES}
    if pins!=st['permittedFiles']:
        raise ValueError('Delivered bytes differ from the frozen local F2 file pins')
    rows=read(folder/FILES[0])
    if (len(rows)!=350 or len({r['id'] for r in rows})!=350 or
            any(set(r)!={'id','text'} or not re.fullmatch('[a-f0-9]{64}',r['id']) for r in rows)):
        raise ValueError('Only 350 opaque IDs and their report texts may be released')
    result={'at':datetime.now(UTC).isoformat(),'selectionPin':selection,'files':pins}
    save(folder/'accepted.json',result)
    return result


def wait_for_release(root,out,binding,guard):
    source=read(root/'inputs'/binding['manifest'])
    permitted=source['provenance']['permittedF2Files']
    selection=digest(out/'development-selection.json')
    save(out/'F2-awaiting.json',{'entryPin':binding['sourcePin'],'selectionPin':selection,'permittedFiles':permitted})
    folder=root/'F2-release'
    while not (folder/'accepted.json').exists():
        guard.check()
        time.sleep(5)
    receipt=read(folder/'accepted.json')
    if (receipt['selectionPin']!=selection or receipt['files']!=permitted or
            any(digest(folder/n)!=permitted[n] for n in FILES)):
        raise ValueError('F2 release does not bind these development decisions')
    return tuple(read(folder/n) for n in FILES)


def watch(local,commit,expected):
    if os.name!='nt' or not re.fullmatch('[a-f0-9]{40}',commit):
        raise ValueError('Workstation boundary monitor and exact code commit required')
    from word_table_lane import identity, lease

    py=Path(__file__).resolve()
    audit=local/'release-monitor.json'
    if local.resolve()!=(Path.cwd()/'.local/word-table/F2-release-local').resolve():
        raise ValueError('Unexpected private release directory')
    remote_script=f'{REMOTE}/code/{commit}/{py.name}'
    cmd=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','spark',ENV,remote_script]
    news={'owner':identity(),'at':datetime.now(UTC).isoformat(),'commit':commit,'expectedEntryPin':expected}
    with lease(local/'monitor.lock'):
        save(audit,{**news,'status':'waiting for development selection'})
        while not (local.parent/'STOP').exists():
            try:
                response=subprocess.run([*cmd,'status'],capture_output=True,text=True,timeout=60,check=False)
            except subprocess.TimeoutExpired:
                time.sleep(120)
                continue
            if response.returncode:
                time.sleep(120)
                continue
            state=json.loads(response.stdout)
            if state['terminal']:
                save(audit,{**news,'status':'terminal before transfer'})
                return
            if state['ready']:
                if state['entryPin']!=expected or state['permittedFiles']!={n:digest(local/n) for n in FILES}:
                    raise ValueError('Remote selection binding or local file pin differs')
                subprocess.run(['ssh','-o','BatchMode=yes','spark','mkdir','-p',REMOTE+'/F2-release'],check=True)
                subprocess.run(['scp','-B',*[str(local/n) for n in FILES],'spark:'+REMOTE+'/F2-release/'],check=True)
                receipt=subprocess.run([*cmd,'accept',state['selectionPin']],check=True,capture_output=True,text=True)
                save(audit,{**news,'status':'delivered after frozen selection','receipt':json.loads(receipt.stdout)})
                return
            time.sleep(120)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['status','accept','watch'])
    parser.add_argument('args',nargs='*')
    arg=parser.parse_args()
    if arg.mode=='watch':
        watch(Path(arg.args[0]),*arg.args[1:])
    elif arg.mode=='status':
        print(json.dumps(status(Path(REMOTE))))
    else:
        print(json.dumps(accept(Path(REMOTE),arg.args[0])))
