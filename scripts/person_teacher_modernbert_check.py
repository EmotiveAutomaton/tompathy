"""Optional Q13 engineering prerequisite on an independent local Spark copy.

Run once in the Q13 slot after Q12. The fixture contains no study reports.
The existing November 20 fine runtime is imported only from its registered directory.
"""
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path

NEW=Path('/home/agent/tompathy-open/person-teacher-20261121')
OLD=Path('/home/agent/tompathy-open/word-table-20261120')
REPAIR='549a22cb1ce98382120f3697844302a0f0e90655'
ORIGINAL='51c188e92b3473af802af78fd3ec4b10baceef0b13fc783516c4ef3c445194fe'


def read(path):
    return json.loads(path.read_bytes())


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def eligible():
    own=Path(__file__).resolve()
    if not re.fullmatch('[0-9a-f]{40}',own.parent.name) or own.parent.parent!=NEW/'code':
        raise ValueError('Use a committed, registered Spark snapshot')
    cfg=read(NEW/'q13-copy-registration.json')
    if cfg['commit']!=own.parent.name or cfg['scriptPin']!=digest(own):
        raise ValueError('Copy-test registration differs')
    if any(p.exists() for p in [NEW/'STOP',OLD/'STOP',NEW/'tail/STOP']):
        raise ValueError('Owner STOP')
    q=NEW/'jobs/Q12'
    owner=read(q/'owner.json')
    release=read(q/'released.json')
    if (owner!=release['owner'] or release['nativeExitCode']!=0 or not release['descriptorClosed']
        or owner['bootId']!=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
        or read(q/'complete.json')['receiptPin']!=digest(q/'receipt.json') or read(q/'receipt.json')['status']!='complete'):
        raise ValueError('Q12 needs a verified terminal release first')
    proc=Path('/proc')/str(owner['pid'])/'stat'
    if proc.exists() and proc.read_text().rsplit(') ',1)[1].split()[19]==str(owner['startTicks']):
        raise ValueError('Q12 native worker remains active')
    if (NEW/'jobs/Q7/owner.json').exists():
        raise ValueError('The conditional Q13 slot has already passed')
    return cfg


def proof():
    cfg=eligible()
    code=OLD/'code'/REPAIR
    sys.path.insert(0,str(code))
    import word_table_fine_runtime as runtime
    import word_table_g2_repair as repair
    import word_table_lane as lane
    lane.settings()
    # Preflight verifies the exact registered compiler, package, headers, prior failed run and original models.
    prev,_,source_dir=repair.preflight(lane)
    if prev['commit']!=REPAIR or digest(source_dir/'source.json')!=ORIGINAL:
        raise ValueError('Original training source differs')
    folder=NEW/'engineering/Q13-copy-a'
    with lane.lease(Path('/home/agent/gpu.lock')):
        eligible()
        folder.mkdir(parents=True,exist_ok=False)
        owner={**lane.identity(),'job':'Q13-copy','commit':cfg['commit'],'lock':'/home/agent/gpu.lock','at':lane.now()}
        lane.write(folder/'owner.json',owner)
        try:
            with lane.core.Guard(folder,.5) as thermal:
                guard=lane.Checks(NEW,folder,thermal)
                guard.check()
                if lane.core.api('ps')['models']:
                    raise ValueError('Spark GPU has a resident model')
                import numpy as np
                import torch
                if not torch.cuda.is_available():
                    raise ValueError('CUDA required to reproduce the original runtime')
                torch.set_num_threads(3)
                torch.set_num_interop_threads(1)
                torch.set_float32_matmul_precision('highest')
                torch.backends.cuda.matmul.allow_tf32=False
                cfg_model=read(source_dir/'source.json')
                copied=folder/'encoder'
                copied.mkdir()
                for name,h in cfg_model['files'].items():
                    guard.check()
                    if Path(name).name!=name or digest(source_dir/'encoder'/name)!=h:
                        raise ValueError('Original model file differs')
                    shutil.copyfile(source_dir/'encoder'/name,copied/name)
                    if digest(copied/name)!=h or os.path.samefile(copied/name,source_dir/'encoder'/name):
                        raise ValueError('Expected independent exact local copy')
                encoder,targets,_,_=runtime.components()
                shares=np.zeros((16,9))
                shares[np.arange(len(shares)),np.arange(len(shares))%9]=1
                spec=targets.training_targets(shares,np.zeros(16),np.repeat('go',16),'sigmoid')
                model,opt=encoder.load_original(copied,spec,'cuda',cfg_model['files'],guard.check,seed=23)
                model.train()
                texts=['A train arrived.' if i%2 else 'The hillside was still in the morning light.' for i in range(16)]
                previous=model.head.weight.detach().clone()
                guard.check()
                logits=model(texts)
                gold=torch.as_tensor(spec['targets'],device='cuda',dtype=logits.dtype)
                weights=torch.as_tensor(spec['weights'],device='cuda',dtype=logits.dtype)
                loss=targets.weighted_loss(logits,gold,weights,'sigmoid')
                loss.backward()
                grad=torch.nn.utils.clip_grad_norm_(model.parameters(),1.,error_if_nonfinite=True)
                opt.step()
                torch.cuda.synchronize()
                guard.check()
                delta=float((model.head.weight.detach()-previous).abs().max().cpu())
                if not (np.isfinite(delta) and delta>0 and float(grad)>0 and torch.isfinite(loss)):
                    raise ValueError('Training copy did not complete a finite optimizer update')
                result={'status':'verified','sourcePin':ORIGINAL,'priorRuntimeCommit':REPAIR,'owner':owner,
                        'examples':16,'sourceFiles':len(cfg_model['files']),'derivedFromStudyData':False,
                        'loss':float(loss.detach().cpu()),'gradientNorm':float(grad),'maximumHeadChange':delta}
                lane.write(folder/'verified.json',result)
        except Exception as exc:
            lane.write(folder/'failed.json',{'owner':owner,'reason':str(exc)})
            raise


if __name__=='__main__':
    try:
        proof()
    except Exception as exc:
        lane=sys.modules.get('word_table_lane')
        if lane and isinstance(exc,lane.Busy):
            sys.exit(74)
        raise
