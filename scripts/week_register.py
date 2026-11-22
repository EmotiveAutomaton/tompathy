"""Create a size-capped allowlist of open Spark inputs from verified local preparation."""
import io
import json
import subprocess
import tarfile
from pathlib import Path

from cb_inputs import pin

WEEK=Path('.local/week-20261122')
FROZEN=Path('.local/nine-channel/tp30-frozen-a')
READERS={'base':Path('.local/readers/models/minilm'),
         'need':Path('.local/nine-channel/c0-b/rp-need-1'),
         'worry':Path('.local/trigger/export-worry-a/rp-worry-1')}
SCRIPTS=('scripts/week_spark.py','scripts/week_dispatch.py','scripts/word_table_lane.py',
         'scripts/spark-reader-job.py','engine/tompathy_engine/eval/readers/tp31_teacher.py')


def prepare():
    import hashlib
    sha=lambda b:hashlib.sha256(b).hexdigest()
    read=lambda p:json.loads(p.read_bytes())
    commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    if pin(FROZEN/'receipt.json')!='d04658e1c84ef10e0c95847947359b24da91b79368bd91b3fa22da2d70c3e250':
        raise ValueError('Training source differs')
    frozen=read(FROZEN/'receipt.json')
    code={}; models={}; manifests={}
    def include(tar,path,name,h):
        if path.is_symlink() or pin(path)!=h:
            raise ValueError('Changed artifact: '+name)
        tar.add(path,name,recursive=False)
    def raw(tar,name,b):
        entry=tarfile.TarInfo(name)
        entry.size=len(b)
        tar.addfile(entry,io.BytesIO(b))
    with tarfile.open(WEEK/'open-inputs-a.tar','x') as tar:
        for s in SCRIPTS:
            b=subprocess.check_output(['git','show',commit+':'+s])
            name=Path(s).name
            raw(tar,'code/'+name,b)
            code[name]=sha(b)
        for job in ('Q20','Q21','Q22'):
            folder=WEEK/(job+'-inputs-a')
            h=pin(folder/'receipt.json')
            if (read(folder/'complete.json')['sourceReceiptPin']!=h or
                read(folder/'exit-verification.json')['releasePin']!=pin(folder/'released.json')):
                raise ValueError('Unverified preparation job '+job)
            r=read(folder/'receipt.json')
            files=r['shards'] if job=='Q20' else r['files']
            for name,value in files.items():
                if Path(name).name!=name:
                    raise ValueError('Invalid input shard name')
                include(tar,folder/'spark-inputs'/name,job+'-inputs/'+name,value)
            b=json.dumps(dict(counts=r['counts'],files=files,sourceReceiptPin=h)).encode()
            raw(tar,job+'-inputs.json',b)
            manifests[job]=sha(b)
        for key,p in READERS.items():
            if key=='base':
                files=frozen['vectors']['encoder']['files']
                root=p
            else:
                m=read(p/'pack.json')
                if m['encoder']['files']['encoder/model.safetensors']!={
                    'need':'53aa51172d142c89d9012cce15ae4d6cc0ca6895895114379cacb4fab128d9db',
                    'worry':'4250c91e06fd7eba3f79728a034f01eb1e691d5b9d7a5cb5548f2f4c9ed31ceb'}[key]:
                    raise ValueError('Component encoder changed')
                files={n.removeprefix('encoder/'):v for n,v in m['encoder']['files'].items()
                       if n.startswith('encoder/') and '/.cache/' not in n}
                root=p/'encoder'
            for n,h in files.items():
                if Path(n).is_absolute() or '..' in Path(n).parts:
                    raise ValueError('Unconfined encoder file')
                include(tar,root/n,'models/'+key+'/'+n,h)
                models[key+'/'+n]=h
        if pin(FROZEN/'artifact-manifest.json')!=frozen['artifactsPin']:
            raise ValueError('Channel inventory differs')
        heads=[(READERS['need']/'head.npz','tags.npz','7f5bfe1ff5ab5e4a0b93072bb7e1f54f73466ab01ade90fc2ad2c4041d12e7ae'),
               (READERS['worry']/'head.npz','worry.npz','a8769895cff71ba61bf5a29262a8bac97c94377f11e39760c845f7d7055411b1'),
               (FROZEN/'go_plus_envent-profile-head.npz','channels.npz',
                read(FROZEN/'artifact-manifest.json')['files']['go_plus_envent-profile-head.npz'])]
        for p,n,h in heads:
            include(tar,p,'models/'+n,h)
            models[n]=h
        cfg=dict(commit=commit,code=code,manifests=manifests,models=models,endUTC=1795795200,
                 scipyWheel='3c085faa2cfa879c5141df483f836f4d691045a078224a670fa570fa01612d89')
        b=(json.dumps(cfg,sort_keys=True,indent=2)+'\n').encode()
        raw(tar,'registration.json',b)
    pkg=WEEK/'open-inputs-a.tar'
    if pkg.stat().st_size>=1_000_000_000:
        raise ValueError('Transfer exceeds the cap')
    (WEEK/'registration.json').write_bytes(b)
    print(commit,sha(b),pkg.stat().st_size,pin(pkg))


if __name__=='__main__':
    prepare()
