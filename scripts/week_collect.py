"""Transfer verified weekly Spark outputs; keep reusable embedding caches on Spark."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT=Path('/home/agent/tompathy-open/week-20261122')
LOCAL=Path('.local/week-20261122')
CAP=1_000_000_000
REG='22e90646c03230dd8c00fe1cb98ff38149adc445467fd11c8050916ca8fcfbb9'


def pin(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def export(job):
    src=ROOT/'jobs'/job
    if not (src/'released.json').exists():
        return {'ready':False}
    owner,rel=read(src/'owner.json'),read(src/'released.json')
    if (owner['registration']!=REG or pin(ROOT/'registration.json')!=REG
        or owner!=rel['owner'] or owner['job']!=job or not rel['descriptorClosed']
        or Path('/proc/sys/kernel/random/boot_id').read_text().strip()!=owner['bootId']):
        raise ValueError('Wrong worker, boot or release')
    pid=str(owner['pid'])
    stat=Path('/proc')/pid/'stat'
    if stat.exists() and stat.read_text().rsplit(')',1)[1].split()[19]==str(owner['startTicks']):
        raise ValueError('Worker still running')
    gpu=Path('/home/agent/gpu.lock').stat()
    for line in Path('/proc/locks').read_text().splitlines():
        parts=line.split()
        if len(parts)>5 and parts[1]=='FLOCK' and parts[4]==pid:
            major,minor,inode=parts[5].split(':')
            if (int(major,16),int(minor,16),int(inode))==(os.major(gpu.st_dev),os.minor(gpu.st_dev),gpu.st_ino):
                raise ValueError('Worker still owns GPU lease')
    if rel['nativeExitCode']:
        return dict(ready=False,failed=True,owner=owner,release=rel)
    h=pin(src/'receipt.json')
    r=read(src/'receipt.json')
    if read(src/'complete.json')['sourceReceiptPin']!=h or r['owner']!=owner or r['status']!='complete':
        raise ValueError('Incomplete scientific receipt')
    files={}
    total=0
    for p in sorted(src.rglob('*')):
        if p.is_symlink():
            raise ValueError('Symlink in job')
        if not p.is_file() or 'vectors' in p.relative_to(src).parts:
            continue
        total+=p.stat().st_size
        if total>=CAP:
            raise ValueError('Compact result exceeds transfer cap')
        files[p.relative_to(src).as_posix()]=pin(p)
    if any(files.get(k)!=v for k,v in r['outputs'].items()):
        raise ValueError('Completed outputs changed')
    archive=ROOT/(job+'-'+h+'.tgz')
    if not archive.exists():
        tmp=archive.with_suffix('.partial')
        with tarfile.open(tmp,'w:gz',compresslevel=1) as t:
            for k in files:
                t.add(src/k,k,recursive=False)
        tmp.replace(archive)
    if archive.stat().st_size+len(json.dumps(files).encode())>=CAP:
        raise ValueError('Compressed transfer exceeds cap')
    return dict(ready=True,owner=owner,release=rel,sourceReceiptPin=h,files=files,
                bytes=archive.stat().st_size,archivePin=pin(archive),name=archive.name)


def collect(job):
    record=LOCAL/(job+'-transfer.json')
    if record.exists():
        return read(record)
    result=subprocess.run(['ssh','-o','BatchMode=yes','spark','python3','-','export',job],
        input=Path(__file__).read_bytes(),capture_output=True,check=True)
    r=json.loads(result.stdout)
    if not r['ready']:
        return r
    h=r['sourceReceiptPin']
    if (len(h)!=64 or any(c not in '0123456789abcdef' for c in h)
        or r['name']!=job+'-'+h+'.tgz' or r['bytes']+len(result.stdout)>=CAP):
        raise ValueError('Unexpected Spark archive')
    archive=LOCAL/r['name']
    if not archive.exists():
        tmp=archive.with_suffix('.download')
        subprocess.run(['scp','-B','spark:'+ROOT.as_posix()+'/'+r['name'],str(tmp)],check=True)
        if pin(tmp)!=r['archivePin']:
            raise ValueError('Download hash differs')
        tmp.replace(archive)
    if pin(archive)!=r['archivePin']:
        raise ValueError('Archive changed')
    dest=LOCAL/('verified-'+job+'-'+h[:12])
    dest.mkdir(exist_ok=True)
    seen=set()
    with tarfile.open(archive,'r:gz') as t:
        for m in t:
            p=(dest/m.name).resolve()
            if (not m.isfile() or not p.is_relative_to(dest.resolve()) or m.name not in r['files']
                or m.name in seen or ':' in m.name or '\\' in m.name):
                raise ValueError('Unexpected archive member')
            seen.add(m.name)
            if not p.exists():
                p.parent.mkdir(parents=True,exist_ok=True)
                tmp=p.with_suffix(p.suffix+'.part')
                with tmp.open('wb') as f,t.extractfile(m) as source:
                    shutil.copyfileobj(source,f)
                if pin(tmp)!=r['files'][m.name]:
                    raise ValueError('Member hash differs')
                tmp.replace(p)
            if pin(p)!=r['files'][m.name]:
                raise ValueError('Local member changed')
    if seen!=set(r['files']) or seen!={p.relative_to(dest).as_posix() for p in dest.rglob('*') if p.is_file()}:
        raise ValueError('Incomplete transfer')
    r.update(mirror=dest.as_posix(),nativeExited=True,priorFlockReleased=True)
    with record.open('x',encoding='utf8') as f:
        json.dump(r,f)
    return r


if __name__=='__main__':
    mode,job=sys.argv[1:]
    if job not in ('Q20','Q21','Q22'):
        raise ValueError('Unknown job')
    if mode=='export':
        print(json.dumps(export(job)))
    elif mode=='collect':
        r=collect(job)
        print({k:r.get(k) for k in ('ready','failed','sourceReceiptPin','mirror')})
