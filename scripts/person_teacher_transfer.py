"""Copy one completed open-study job from a pinned Spark directory, below the November 21 limit."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import tarfile
from pathlib import Path, PurePosixPath

REMOTE = Path('/home/agent/tompathy-open')
LOCAL = Path('.local')
CAP = 1_000_000_000
COMMIT = 'ff2e4dd0f02fb9488e35ce4acf580ce0bad73d53'
Q6_COMMIT = '992b1b683b434914ffe39e2b75f2ec5a5c35506c'
BOOT = '17b89c07-ca2a-4328-be23-1079536e9232'
ROOTS = {'Q6':'word-table-20261120', **{j:'person-teacher-20261121' for j in ('Q11','Q4','Q12','Q13','Q7')}}
SSH = ['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','spark']


def pin(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def save(path, data):
    if path.is_file():
        if read(path)!=data:
            raise ValueError('Existing audit differs: '+path.name)
        return
    with path.open('x',encoding='utf8') as stream:
        json.dump(data,stream,sort_keys=True,allow_nan=False)


def inspect_remote(job):
    if os.name=='nt':
        raise RuntimeError('Native Spark inspection required')
    os.nice(8)
    root = REMOTE/ROOTS[job]
    folder = root/'jobs'/job
    if not (folder/'released.json').is_file() or not any((folder/n).is_file() for n in ('complete.json','failed.json')):
        return {'ready':False,'job':job}
    owner,release,receipt=[read(folder/n) for n in ('owner.json','released.json','receipt.json')]
    if not (owner==release['owner']==receipt['owner'] and owner['job']==job and release['descriptorClosed']
            and owner['bootId']==BOOT==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
            and owner['lock']=='/home/agent/gpu.lock' and owner['commit']==(Q6_COMMIT if job=='Q6' else COMMIT)):
        raise ValueError('Remote source identity or descriptor release differs')
    if job=='Q6':
        if (owner['pid'],str(owner['startTicks']))!=(2970443,'20817696') or receipt['entry']!=read(root/'queue.json')['jobs'][job]:
            raise ValueError('Q6 launch identity differs')
        events=[json.loads(line) for line in (root/'events.jsonl').read_text().splitlines() if line.strip()]
        if not any(e.get('job')==job and e.get('event')=='exit' and e.get('pid')==owner['pid'] and
                   e.get('code')==release['nativeExitCode'] for e in events):
            return {'ready':False,'job':job}
    stat=Path('/proc')/str(owner['pid'])/'stat'
    if stat.exists() and stat.read_text().rsplit(') ',1)[1].split()[19]==str(owner['startTicks']):
        raise ValueError('Original process is still alive')
    lock=Path(owner['lock']).stat()
    for line in Path('/proc/locks').read_text().splitlines():
        fields=line.split()
        if len(fields)>5 and fields[1]=='FLOCK' and fields[4]==str(owner['pid']):
            maj,minor,ino=fields[5].split(':')
            if (int(maj,16),int(minor,16),int(ino))==(os.major(lock.st_dev),os.minor(lock.st_dev),lock.st_ino):
                raise ValueError('Original owner still holds the GPU flock')
    terms=[n for n in ('complete.json','failed.json') if (folder/n).exists()]
    if (len(terms)!=1 or read(folder/terms[0])['receiptPin']!=pin(folder/'receipt.json')
            or (terms[0]=='complete.json' and release['nativeExitCode']!=0)):
        raise ValueError('Invalid terminal receipt')
    entries=sorted(folder.rglob('*'))
    if any(p.is_symlink() or not(p.is_dir() or p.is_file()) for p in entries):
        raise ValueError('Unexpected filesystem entry in receipt directory')
    files=[p for p in entries if p.is_file()]
    nbytes=sum(p.stat().st_size for p in files)
    if nbytes>=CAP:
        raise ValueError('Source is at or above the storage transfer cap')
    pins={p.relative_to(folder).as_posix():pin(p) for p in files}
    if 'artifactsPin' in receipt and (pins['artifacts.json']!=receipt['artifactsPin'] or any(
            pins.get(k)!=v for k,v in read(folder/'artifacts.json')['files'].items())):
        raise ValueError('Source artifact seal differs')
    archive=root/('transfer-'+job+'-'+pins['receipt.json']+'.tgz')
    if not archive.exists():
        temp=archive.with_suffix('.partial-'+str(os.getpid()))
        with tarfile.open(temp,'x:gz',compresslevel=1) as tar:
            for path in files:
                tar.add(path,arcname=path.relative_to(folder).as_posix(),recursive=False)
        temp.rename(archive)
    if archive.stat().st_size>=CAP or archive.stat().st_size+len(json.dumps(pins).encode())>=CAP:
        raise ValueError('Archive and inventory exceed the transfer cap')
    return {'ready':True,'owner':owner,'release':release,'nativeExited':True,'priorFlockReleased':True,
            'sourceReceiptPin':pins['receipt.json'],'terminal':terms[0],'status':receipt['status'],'files':pins,
            'sourceBytes':nbytes,'archive':str(archive),'archiveBytes':archive.stat().st_size,'archivePin':pin(archive)}


def fetch(job):
    base=LOCAL/('word-table' if job=='Q6' else 'person-teacher')
    audit=base/(job+'-transfer-a.json')
    if audit.exists():
        data=read(audit)
        if pin(Path(data['mirror'])/'receipt.json')!=data['sourceReceiptPin'] or pin(Path(data['inventory']))!=data['inventoryPin']:
            raise ValueError('Prior verified mirror changed')
        return True
    if job=='G4':
        folder=base/'jobs/G4'
        if not (folder/'released.json').exists():
            return False
        sys.path.insert(0,'E:/EmotiveAutomaton/Projects/SoundingLine/sounding-line')
        from runners.stage9.process_identity import native_identity
        owner,release,receipt=[read(folder/n) for n in ('owner.json','released.json','receipt.json')]
        alive=native_identity(owner['pid'])
        if (owner!=release['owner'] or owner!=receipt['owner'] or not release['descriptorClosed']
                or release['nativeExitCode'] or (owner['pid'],owner['createdTicks'])!=(197384,134397443903692431)
                or owner['commit']!=COMMIT or (alive and alive['created_ticks']==owner['createdTicks'])
                or Path(owner['lock']).resolve()!=(LOCAL/'word-table/workstation/gpu.lock').resolve()
                or read(folder/'complete.json')['receiptPin']!=pin(folder/'receipt.json')):
            raise ValueError('G4 native identity or release differs')
        import msvcrt
        with Path(owner['lock']).open('r+b') as stream:
            msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1)
            msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)
        files={p.relative_to(folder).as_posix():pin(p) for p in sorted(folder.rglob('*')) if p.is_file()}
        data={'owner':owner,'release':release,'status':receipt['status'],'sourceReceiptPin':files['receipt.json'],
              'nativeExited':True,'priorFlockReleased':True,'terminal':'complete.json'}
    else:
        result=subprocess.run([*SSH,'/home/agent/venvs/engine/bin/python','-','--native',job],
                              input=Path(__file__).read_bytes(),stdout=subprocess.PIPE,check=True)
        data=json.loads(result.stdout)
        if not data['ready']:
            return False
        files=data.pop('files')
        expected='/home/agent/tompathy-open/'+ROOTS[job]+'/transfer-'+job+'-'+data['sourceReceiptPin']+'.tgz'
        if (data['archive']!=expected or data['sourceBytes']>=CAP or data['archiveBytes']+len(result.stdout)>=CAP):
            raise ValueError('Unregistered source or transfer size')
        archive=base/('transfer-'+job+'-'+data['archivePin']+'.tgz')
        if not archive.exists():
            partial=archive.with_suffix('.partial')
            if partial.exists():
                raise ValueError('Partial download preserved; review before transfer')
            subprocess.run(['scp','-B','-o','ConnectTimeout=15','spark:'+expected,str(partial)],check=True)
            if partial.stat().st_size!=data['archiveBytes'] or pin(partial)!=data['archivePin']:
                raise ValueError('Archive download changed')
            partial.rename(archive)
        if pin(archive)!=data['archivePin']:
            raise ValueError('Existing archive differs')
        folder=base/('verified-spark-'+job+'-a')
        folder.mkdir(exist_ok=True)
        seen=set()
        with tarfile.open(archive,'r:gz') as tar:
            for member in tar:
                key=member.name
                parts=PurePosixPath(key).parts
                if (not member.isfile() or key not in files or key in seen or not parts or
                        any(v in ('','..','.') or ':' in v or '\\' in v for v in parts) or PurePosixPath(key).is_absolute()):
                    raise ValueError('Unexpected archive member')
                path=folder.joinpath(*parts)
                if not path.resolve().is_relative_to(folder.resolve()):
                    raise ValueError('Archive path escapes mirror')
                seen.add(key)
                if not path.exists():
                    path.parent.mkdir(parents=True,exist_ok=True)
                    with path.open('xb') as w, tar.extractfile(member) as r:
                        import shutil
                        shutil.copyfileobj(r,w)
                if pin(path)!=files[key]:
                    raise ValueError('Copied file differs: '+key)
        if seen!=set(files) or {p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()}!=seen:
            raise ValueError('Mirror inventory differs')
    inventory=base/(job+'-transfer-a-pins.json')
    save(inventory,files)
    data.update(mirror=folder.as_posix(),verifiedFiles=len(files),inventory=inventory.as_posix(),inventoryPin=pin(inventory))
    save(audit,data)
    return True


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--native',action='store_true')
    parser.add_argument('job',choices=[*ROOTS,'G4'])
    args=parser.parse_args()
    if args.native:
        print(json.dumps(inspect_remote(args.job)))
    else:
        print(json.dumps({'job':args.job,'verified':fetch(args.job)}))
