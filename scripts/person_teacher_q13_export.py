"""Size-capped export of Q13 evidence and saved predictions; weights stay on Spark."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

BASE=Path('.local/person-teacher')
ROOT=Path('/home/agent/tompathy-open/person-teacher-20261121')
LIMIT=1_000_000_000


def read(p):
    return json.loads(p.read_bytes())


def pin(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()


def native():
    cfg=read(ROOT/'q13-copy-registration.json')
    folder=ROOT/'tail/Q13-modernbert'
    if not (folder/'released.json').exists():
        return {'ready':False,'copyReview':(ROOT/'tail/copy-exit.json').is_file() and read(ROOT/'tail/copy-exit.json')['code']!=0}
    boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    lock=Path('/home/agent/gpu.lock').stat()
    def verified_exit(directory):
        owner,release=read(directory/'owner.json'),read(directory/'released.json')
        if (release['owner']!=owner or not release['descriptorClosed'] or owner['bootId']!=boot
                or owner['commit']!=cfg['commit'] or owner['lock']!='/home/agent/gpu.lock'):
            raise ValueError('Q13 source owner or descriptor release differs')
        proc=Path('/proc')/str(owner['pid'])/'stat'
        if proc.exists() and proc.read_text().rsplit(') ',1)[1].split()[19]==str(owner['startTicks']):
            raise ValueError('Q13 source worker has not exited')
        for ln in Path('/proc/locks').read_text().splitlines():
            cols=ln.split()
            if len(cols)>=6 and cols[1]=='FLOCK' and cols[4]==str(owner['pid']):
                a,b,c=cols[5].split(':')
                if (int(a,16),int(b,16),int(c))==(os.major(lock.st_dev),os.minor(lock.st_dev),lock.st_ino):
                    raise ValueError('Source GPU flock remains held')
        return owner,release
    copy=ROOT/'engineering/Q13-copy-a'
    prior,release=verified_exit(copy)
    owner,end=verified_exit(folder)
    receipt=read(folder/'receipt.json')
    if (read(copy/'verified.json')['owner']!=prior or release['nativeExitCode'] or receipt['owner']!=owner
            or receipt['copyPin']!=pin(copy/'verified.json') or boot!=cfg['priorDispatcher']['bootId']):
        raise ValueError('Wrong copy verification or training source')
    if receipt['status']!='complete':
        return {'ready':False,'failed':True,'sourceReceiptPin':pin(folder/'receipt.json')}
    if end['nativeExitCode'] or read(folder/'complete.json')['receiptPin']!=pin(folder/'receipt.json'):
        raise ValueError('Training completion mismatch')
    paths=sorted(p for p in folder.rglob('*') if p.is_file())
    if any(p.is_symlink() for p in paths) or sum(p.stat().st_size for p in paths)>=LIMIT:
        raise ValueError('Compact Q13 export exceeds the cap or has a symlink')
    inventory={p.relative_to(folder).as_posix():pin(p) for p in paths}
    if (receipt['forecastPin']!=inventory['forecast-inventory.json'] or
            receipt['sources']!=inventory['complete-storage-inventory.json']):
        raise ValueError('Original storage or compact forecast seal differs')
    complete=read(folder/'complete-storage-inventory.json')
    for k,v in read(folder/'forecast-inventory.json').items():
        if complete.get(k)!=v or inventory.get('forecasts/'+k)!=v:
            raise ValueError('Compact forecast differs from the sealed heavy run')
    archive=ROOT/'tail'/('compact-'+pin(folder/'receipt.json')+'.tgz')
    if not archive.exists():
        temporary=archive.with_suffix('.partial')
        with tarfile.open(temporary,'x:gz',compresslevel=1,dereference=True) as stream:
            for p in paths:
                stream.add(p,arcname=p.relative_to(folder).as_posix(),recursive=False)
        temporary.rename(archive)
    if archive.stat().st_size+len(json.dumps(inventory).encode())>=LIMIT:
        raise ValueError('Compressed Q13 archive and inventory exceed the cap')
    return {'ready':True,'owner':owner,'release':end,'copy':read(copy/'verified.json'),'copyExit':release,
            'nativeExited':True,'priorFlockReleased':True,'sourceReceiptPin':inventory['receipt.json'],
            'files':inventory,'archivePin':pin(archive),'archiveBytes':archive.stat().st_size,'archive':str(archive)}


def fetch():
    target=BASE/'Q13-modernbert-transfer.json'
    if target.exists():
        return read(target)
    result=subprocess.run(['ssh','-o','BatchMode=yes','spark','/home/agent/venvs/engine/bin/python','-','--native'],
                          input=Path(__file__).read_bytes(),capture_output=True,check=True)
    data=json.loads(result.stdout)
    if not data['ready']:
        return data
    h=data['sourceReceiptPin']
    if (len(h)!=64 or any(c not in '0123456789abcdef' for c in h) or
            data['archive']!='/home/agent/tompathy-open/person-teacher-20261121/tail/compact-'+h+'.tgz'
            or data['archiveBytes']+len(result.stdout)>=LIMIT):
        raise ValueError('Unexpected Q13 export or size')
    archive=BASE/('q13-compact-'+h+'.tgz')
    if not archive.exists():
        subprocess.run(['scp','-B','spark:'+data['archive'],str(archive)],check=True)
    if pin(archive)!=data['archivePin']:
        raise ValueError('Downloaded Q13 archive differs')
    folder=BASE/'verified-spark-Q13-modernbert-a'
    folder.mkdir(exist_ok=True)
    inventory=data.pop('files')
    seen=set()
    with tarfile.open(archive,'r:gz') as stream:
        for member in stream:
            key=member.name
            path=(folder/key).resolve()
            if (not member.isfile() or key in seen or key not in inventory or
                    not path.is_relative_to(folder.resolve()) or ':' in key or '\\' in key):
                raise ValueError('Unexpected archive entry')
            seen.add(key)
            if not path.exists():
                path.parent.mkdir(parents=True,exist_ok=True)
                with path.open('xb') as dest,stream.extractfile(member) as src:
                    shutil.copyfileobj(src,dest)
            if pin(path)!=inventory[key]:
                raise ValueError('Local Q13 forecast or record differs')
    if seen!=set(inventory) or seen!={p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()}:
        raise ValueError('Q13 compact transfer incomplete')
    data['verifiedFiles']=len(seen)
    data['mirror']=folder.as_posix()
    with target.open('x',encoding='utf8') as f:
        json.dump(data,f,indent=2)
    return data


if __name__=='__main__':
    if sys.argv[1:]==['--native']:
        print(json.dumps(native()))
    else:
        result=fetch()
        print(json.dumps({k:result.get(k) for k in ('ready','copyReview','failed','verifiedFiles','sourceReceiptPin')}))
