"""Install a checked queue extension without replacing any prior job or input."""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def save(path,value):
    with path.open('x',encoding='utf8',newline='\n') as stream:
        json.dump(value,stream,ensure_ascii=False,allow_nan=False,indent=2)
        stream.write('\n')


def prepare(root, lane, group, specification, destination):
    repo = Path(__file__).resolve().parents[1]
    commit = subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
    destination.mkdir(parents=True,exist_ok=False)
    code = destination/'code'/commit
    code.mkdir(parents=True)
    paths = ['scripts/spark-reader-job.py','scripts/word_table_lane.py','scripts/word_table_register.py',
             *specification['modules']]
    for source_path in paths:
        target = code/Path(source_path).name
        data = subprocess.check_output(['git','show',f'{commit}:{source_path}'],cwd=repo)
        if target.exists():
            raise ValueError('Duplicate module name')
        target.write_bytes(data)
    inputs = destination/'inputs'
    inputs.mkdir()
    opening = read(root/'inputs'/'source.json')
    manifest = {k:opening[k] for k in ('packetPin','lane','packages','environmentPins','publicInputsOnly')}
    if lane!=manifest['lane']:
        raise ValueError('Lane differs from its original environment')
    jobs = {}
    for job, description in specification['jobs'].items():
        files = description['files']
        for name,src in files.items():
            if Path(name).name!=name or name=='source.json':
                raise ValueError('Invalid input name')
            path=Path(src)
            if sha(path)!=specification['pins'][name]:
                raise ValueError(f'Input differs from its intake: {name}')
            if not (inputs/name).exists():
                shutil.copyfile(path,inputs/name)
        primary=job+'.json'
        jobs[job]={'filePin':sha(inputs/primary),'rows':description['rows'],
                   'aux':{k:sha(inputs/k) for k in files if k!=primary}}
    manifest.update(jobs=jobs,provenance=specification['provenance'])
    manifest_name='source-'+group+'.json'
    save(inputs/manifest_name,manifest)
    base={'commit':commit,'manifest':manifest_name,'sourcePin':sha(inputs/manifest_name),
          'codePins':{p.name:sha(p) for p in code.iterdir()}}
    entries={job:dict(base) for job in jobs}
    for job in ('Q4','Q7'):
        if job in entries:
            entries[job].update(q3Entry=dict(entries['Q3']),teacherPin=specification['teacherPin'])
    changes={'lane':lane,'group':group,'entries':entries,'files':{
        p.relative_to(destination).as_posix():sha(p) for p in destination.rglob('*') if p.is_file()}}
    save(destination/'extension.json',changes)
    return sha(destination/'extension.json')


def activate(root, directory, expected):
    manifest = directory/'extension.json'
    if sha(manifest)!=expected:
        raise ValueError('Queue extension transfer mismatch')
    meta=read(manifest)
    for rel,pin in meta['files'].items():
        path=directory/rel
        target=root/rel
        if (not path.resolve().is_relative_to(directory.resolve()) or
                not any(target.resolve().is_relative_to((root/k).resolve()) for k in ('code','inputs')) or
                sha(path)!=pin):
            raise ValueError('Unrecognized or changed transferred file')
        target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():
            with target.open('xb') as f, path.open('rb') as src:
                shutil.copyfileobj(src,f)
        if sha(target)!=pin:
            raise ValueError('Existing immutable queue artifact conflicts')
    # Serialize writers. The existing dispatcher reads the old or new complete file.
    from word_table_lane import lease
    with lease(root/'queue-update.lock'):
        queue=read(root/'queue.json')
        for name, entry in meta['entries'].items():
            if name in queue['jobs'] and queue['jobs'][name]!=entry:
                raise ValueError('Cannot replace a registered job')
            queue['jobs'][name]=entry
        temp=root/('queue-'+meta['group']+'.tmp')
        save(temp,queue)
        os.replace(temp,root/'queue.json')
    return sorted(read(root/'queue.json')['jobs'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['prepare','activate'])
    parser.add_argument('root',type=Path)
    parser.add_argument('group')
    parser.add_argument('directory',type=Path)
    parser.add_argument('spec_or_pin')
    args=parser.parse_args()
    if not re.fullmatch(r'[a-z0-9-]+',args.group):
        parser.error('Invalid group')
    if args.mode=='prepare':
        print(prepare(args.root,args.root.name,args.group,read(Path(args.spec_or_pin)),args.directory))
    else:
        print(activate(args.root,args.directory,args.spec_or_pin))
