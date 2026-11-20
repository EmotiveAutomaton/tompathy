"""Resume the original G3 V5 transport interruption without repeating saved inference."""
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import word_table_lane as lane
from word_table_g3_follow import native_alive
from word_table_rd2 import template

SOURCE_RECEIPT = '0fc5ebb9005cbf7cfc4260ff93a803fb1bb42d7e91ffa4dac40afea8f9fc40cc'
FAILURE = 'c831789a28e565afc7d3b2bc434d159e03f713d278c200d99a39bdfe62070601'
ATTEMPT = 'G3-resume-a'


def source(root):
    parent = root/'jobs/G3'
    old = lane.read(parent/'receipt.json')
    proof = lane.read(root.parent/'g3-v5-timeout-exit-a.json')
    if (lane.pin(parent/'receipt.json') != SOURCE_RECEIPT or lane.pin(parent/'failed.json') != FAILURE
            or lane.read(parent/'failed.json')['receiptPin'] != SOURCE_RECEIPT
            or old['status'] != 'failed' or 'curl: (28)' not in old['reason']
            or proof['sourceReceiptPin'] != SOURCE_RECEIPT or proof['failurePin'] != FAILURE
            or proof['owner'] != old['owner'] or not proof['exactNativeExited'] or not proof['sharedGpuLockReacquired']
            or old['owner'] != lane.read(parent/'owner.json') or native_alive(old['owner'])
            or old['entry'] != lane.read(root/'queue.json')['jobs']['G3']):
        raise ValueError('Failed G3 source or host release differs')
    return old


def restore(parent, out, items, guard):
    """Each original response is independently copied and checked, including the unfinished prefix."""
    copied, complete = {}, {}
    for i, count in enumerate((600, 600, 600, 600, 600, 18)):
        variant = f'V{i}'
        folder = parent/variant/'W'
        protocol = lane.read(folder/'protocol.json')
        binding = {k:v for k,v in protocol.items() if k not in ('prompt','schema','secondKey')}
        durations, valid = lane.completed_prefix(folder, items, binding)
        if len(durations) != count or binding['variant'] != variant or binding['modelPin'] != lane.W[1]:
            raise ValueError('Original G3 prefix or reader differs')
        if (folder/'complete.json').is_file() != (i < 5):
            raise ValueError('Unexpected original terminal variant')
        if i < 5:
            result = lane.read(folder/'complete.json')
            if (result['binding'], result['rows'], result['valid']) != (binding, count, valid):
                raise ValueError('Original variant result differs from its saved responses')
            complete[variant] = result
        for n, path in enumerate(sorted((parent/variant).rglob('*.json'))):
            if n % 32 == 0:
                guard.check()
            if i == 5 and path.name == 'progress.json':
                continue
            relative = path.relative_to(parent)
            dest = out/relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            expected = lane.pin(path)
            if not dest.exists():
                tmp = dest.with_suffix('.restore-tmp')
                shutil.copyfile(path, tmp)
                if lane.pin(tmp) != expected:
                    raise ValueError('Copied G3 artifact changed during restoration')
                tmp.replace(dest)
            if lane.pin(dest) != expected:
                raise ValueError('Restored G3 artifact differs from its source')
            copied[relative.as_posix()] = expected
    return complete, copied


def attempt(root, commit):
    out = root/'jobs'/ATTEMPT
    old = source(root)
    entry = old['entry']
    with lane.lease(root/'gpu.lock'):
        if (out/'complete.json').exists() or (out/'failed.json').exists():
            return 0 if (out/'complete.json').exists() else 1
        out.mkdir(exist_ok=True)
        owner = {**lane.identity(),'job':ATTEMPT,'commit':commit,'at':lane.now(),'lock':str(root/'gpu.lock')}
        lane.write(out/'owner.json',owner)
        lane.append(out/'owners.jsonl',owner)
        continuation = {'attempt':ATTEMPT,'sourceReceiptPin':SOURCE_RECEIPT,'sourceFailurePin':FAILURE,
                        'sourceOwner':old['owner'],'executionCommit':commit,'httpTimeoutSeconds':300,
                        'originalCallsRetained':3018,'originalV5Prefix':18}
        receipt = {'job':'G3','lane':'workstation','entry':entry,'owner':owner,'continuation':continuation,
                   'status':'running'}
        lane.write(out/'receipt.json',receipt)
        try:
            with (out/'owners.jsonl').open() as stream:
                first = datetime.fromisoformat(json.loads(next(stream))['at'])
            hours = 5 - (datetime.now(UTC)-first).total_seconds()/3600
            continuation['boundHoursFromFirstAdmission'] = 5
            with lane.core.Guard(out,hours) as thermal:
                guard = lane.Checks(root,out,thermal)
                guard.check()
                if lane.read(root/'queue.json')['closed'] or (root/'jobs/G3/STOP').exists():
                    raise RuntimeError('Original queue closed or owner requested a stop')
                items, binding = lane.check_entry(root,'G3',entry)
                rows, copies = restore(root/'jobs/G3',out,items,guard)
                lane.write(out/'restored.json',{'files':copies})
                continuation['restoredInventoryPin'] = lane.pin(out/'restored.json')
                lane.write(out/'receipt.json',receipt)
                defs = lane.read(root/'inputs/RD2-prompts.json')
                lengths = lane.read(root/'inputs/RD2-lengths.json')['V5']
                rows['V5'] = lane.rate(root,out/'V5',items,'W','G3',{**binding,'variant':'V5'},guard,
                                       template=template(defs['V5']),token_lengths=lengths,g3_recovery=commit)
                guard.check()
                inventory = {}
                for variant in rows:
                    for n, path in enumerate((out/variant).rglob('*.json')):
                        if n % 64 == 0:
                            guard.check()
                        inventory[path.relative_to(out).as_posix()] = lane.pin(path)
                if any(inventory.get(name) != digest for name,digest in copies.items()):
                    raise ValueError('A previously saved original G3 artifact changed')
                lane.write(out/'artifacts.json',{'files':inventory})
            receipt.update(status='complete',roles=rows,artifactsPin=lane.pin(out/'artifacts.json'))
        except lane.Pause as exc:
            receipt.update(status='paused',reason=str(exc),ended=lane.now())
            lane.write(out/'receipt.json',receipt)
            return 75
        except (OSError, ValueError, RuntimeError, KeyError, TypeError, subprocess.SubprocessError) as exc:
            receipt.update(status='failed',reason=str(exc))
        receipt['ended'] = lane.now()
        lane.write(out/'receipt.json',receipt)
        success = receipt['status'] == 'complete'
        lane.write(out/('complete.json' if success else 'failed.json'),
                   {'at':lane.now(),'receiptPin':lane.pin(out/'receipt.json')})
        return 0 if success else 1


def main():
    root = (Path.cwd()/'.local/word-table/workstation').resolve()
    code = Path(__file__).resolve().parent
    commit = code.name
    if (os.name != 'nt' or code.parent != root/'code' or not re.fullmatch('[0-9a-f]{40}',commit)):
        raise ValueError('Run the frozen workstation repair from the project')
    manifest = lane.read(root/'inputs/G3-resume-a-execution.json')
    if manifest['commit'] != commit or manifest['sourceReceiptPin'] != SOURCE_RECEIPT:
        raise ValueError('Wrong repair snapshot')
    for name, digest in manifest['files'].items():
        if Path(name).name != name or lane.pin(code/name) != digest:
            raise ValueError('Repair snapshot changed')
    lane.settings()
    while True:
        if any((root/p).exists() for p in ('STOP','jobs/G3/STOP',f'jobs/{ATTEMPT}/STOP')) or lane.read(root/'queue.json')['closed']:
            return 1
        try:
            status = attempt(root,commit)
        except lane.Busy:
            status = 74
        if status not in (74,75):
            return status
        time.sleep(600 if status == 75 else 30)


if __name__ == '__main__':
    sys.exit(main())
