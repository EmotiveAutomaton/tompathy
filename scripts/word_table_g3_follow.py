"""Deliver the registered G3 budget check after the frozen workstation dispatcher releases G3."""
import argparse
import ctypes
import os
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path

import word_table_g3_budget as budget
import word_table_lane as lane


def native_alive(owner):
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.OpenProcess(0x101000, False, owner['pid'])
    if not handle:
        if ctypes.get_last_error() == 87:
            return False
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        times = [wintypes.FILETIME() for _ in range(4)]
        if not kernel.GetProcessTimes(handle, *[ctypes.byref(t) for t in times]):
            raise ctypes.WinError(ctypes.get_last_error())
        ticks = times[0].dwHighDateTime << 32 | times[0].dwLowDateTime
        state = kernel.WaitForSingleObject(handle, 0)
        if state not in (0, 258):
            raise ctypes.WinError(ctypes.get_last_error())
        return ticks == owner['createdTicks'] and state == 258
    finally:
        kernel.CloseHandle(handle)


def execution_code(root, entry, after_resume):
    if not after_resume:
        return root/'code'/entry['commit']
    budget.source_folder(root, after_resume)
    registration = root/'inputs'/(budget.JOB+'-after-'+after_resume.removeprefix('G3-')+'-execution.json')
    manifest = lane.read(registration)
    from word_table_g3_resume import SOURCE_RECEIPT
    if manifest['sourceReceiptPin'] != SOURCE_RECEIPT:
        raise ValueError('Engineering handoff has a different source')
    code = root/'code'/manifest['commit']
    if code.parent != root/'code' or len(manifest['commit']) != 40 or not manifest['commit'].isalnum():
        raise ValueError('Invalid engineering execution snapshot')
    for name, digest in manifest['files'].items():
        if Path(name).name != name or lane.pin(code/name) != digest:
            raise ValueError('Engineering handoff code changed')
    return code


def deliver(root, out, control, items, binding, after_resume=None):
    owner = lane.read(out/'owner.json')
    receipt = lane.read(out/'receipt.json')
    complete = (out/'complete.json').is_file()
    terminal = lane.read(out/('complete.json' if complete else 'failed.json'))
    if (terminal.get('receiptPin') != lane.pin(out/'receipt.json') or receipt['owner'] != owner
            or owner['commit'] != execution_code(root,binding,after_resume).name or owner['job'] != budget.JOB
            or Path(owner['lock']).resolve() != (root/'gpu.lock').resolve() or native_alive(owner)):
        raise ValueError('Diagnostic native exit or terminal receipt could not be verified')
    if after_resume and (receipt['entry'] != lane.read(root/'queue.json')['jobs'][budget.JOB]
            or receipt['execution'] != {'commit':owner['commit'],'predecessor':after_resume,'scientificCommit':binding['commit']}):
        raise ValueError('Diagnostic execution or original scientific registration differs')
    # This exact descriptor is available only after the worker has released it.
    with lane.lease(root/'gpu.lock'):
        if complete:
            inventory = out/'artifacts.json'
            if lane.pin(inventory) != receipt['artifactsPin']:
                raise ValueError('Diagnostic inventory changed')
            for name, expected in lane.read(inventory)['files'].items():
                path = (out/name).resolve()
                if not path.is_relative_to(out) or lane.pin(path) != expected:
                    raise ValueError('Diagnostic artifact differs from terminal receipt')
        comparison = None
        if (out/'W/protocol.json').is_file():
            comparison, original_pins = budget.compare(root, out, items, binding, after_resume)
            if original_pins != lane.read(out/'comparison/baseline-pins.json'):
                raise ValueError('Original G3 responses changed')
        if complete and (receipt['status'] != 'complete' or comparison != lane.read(out/'comparison/aggregate.json')
                         or comparison['paired'] != 20 or comparison['higher']['valid'] != receipt['roles']['W']['valid']):
            raise ValueError('Stored aggregate differs from paired response replay')
    result = {'status': receipt['status'], 'sourceReceiptPin': terminal['receiptPin'], 'comparison': comparison}
    if receipt['status'] == 'failed':
        result['partial'] = True
    # Write aggregate data only, after observing the process exit and checking both sets of rows.
    public = root.parents[2]/'docs/exchange/result-sheets/G3-thinking-budget.json'
    if public.exists():
        if lane.read(public) != result:
            raise ValueError('An existing result must be preserved')
    else:
        lane.write(public, result)
    lane.write(control/'verified.json', {'at': lane.now(), 'worker': owner, 'exactNativeExited': True,
               'sharedGpuLockReacquired': True, 'aggregatePin': lane.pin(public), **result})


def follow(root, after_resume=None):
    job = budget.JOB
    control = root/'followups'/(job+'-after-'+after_resume.removeprefix('G3-') if after_resume else job)
    control.mkdir(parents=True, exist_ok=True)
    with lane.lease(control/'delivery.lock'):
        if (control/'verified.json').exists():
            return
        entry = lane.read(root/'queue.json')['jobs'][job]
        code = execution_code(root,entry,after_resume)
        if Path(__file__).resolve() != (code/Path(__file__).name).resolve():
            raise ValueError('Start the committed diagnostic controller')
        items, binding = lane.check_entry(root, job, entry)
        parent = budget.source_folder(root,after_resume)
        out = root/'jobs'/job
        receipt = {'at': lane.now(), 'controller': lane.identity(), 'job': job, 'sourcePin': entry['sourcePin'],
                   'originalOwnerAtRegistration': lane.read(root/'jobs/G3/owner.json'), 'status': 'waiting-for-G3'}
        if after_resume:
            receipt.update(predecessor=after_resume,
                           executionCommit=code.name,studyCommit=entry['commit'])
        lane.write(control/'state.json', receipt)
        try:
            while True:
                if any(path.is_file() for path in (root/'STOP', out/'STOP')) or lane.read(root/'queue.json')['closed']:
                    raise RuntimeError('Queue closed or owner requested a stop')
                if (parent/'failed.json').is_file() or (parent/'skipped.json').is_file():
                    raise RuntimeError('Original G3 did not complete; preserving the pending comparison')
                if (parent/'complete.json').is_file() and not native_alive(lane.read(parent/'owner.json')):
                    break
                if after_resume:
                    wait_state = root/'followups'/after_resume/'state.json'
                    if wait_state.exists() and lane.read(wait_state).get('state') == 'owner stopped':
                        raise RuntimeError('Predecessor received an owner stop')
                time.sleep(30)
            _, receipt['originalReceiptPin'] = budget.terminal_source(root,after_resume)
            receipt.update(status='ready', originalNativeExited=True)
            if after_resume:
                receipt['predecessorOwner'] = lane.read(parent/'owner.json')
            lane.write(control/'state.json', receipt)
            while not (out/'complete.json').exists() and not (out/'failed.json').exists():
                if (root/'STOP').exists() or (out/'STOP').exists() or lane.read(root/'queue.json')['closed']:
                    raise RuntimeError('Queue closed or owner requested a stop')
                command = [sys.executable, '-B', str(code/'word_table_lane.py'), 'worker', str(root), 'workstation', job]
                if after_resume:
                    command.extend(['--after-resume',after_resume])
                status = subprocess.call(command)
                if status in (74, 75):
                    time.sleep(600 if status == 75 else 30)
                elif status != 0 and not (out/'failed.json').exists():
                    raise RuntimeError(f'Diagnostic worker exited before its terminal receipt ({status})')
            # If a newer dispatcher supplied this job, its observed native process can still be exiting.
            for _ in range(120):
                if not native_alive(lane.read(out/'owner.json')):
                    try:
                        deliver(root, out, control, items, binding, after_resume)
                        break
                    except lane.Busy:
                        pass
                time.sleep(5)
            else:
                raise RuntimeError('Terminal job still awaits exact release verification')
            receipt.update(status='verified', verifiedPin=lane.pin(control/'verified.json'))
        except Exception as exc:
            receipt.update(status='stopped', reason=str(exc))
            raise
        finally:
            receipt['updatedAt'] = lane.now()
            lane.write(control/'state.json', receipt)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'follow'))
    parser.add_argument('--after-resume',choices=('G3-resume-a','G3-resume-b'))
    args = parser.parse_args()
    root = (Path.cwd()/'.local/word-table/workstation').resolve()
    if os.name != 'nt' or not (root/'queue.json').is_file():
        parser.error('Run in the registered workstation repository')
    lane.settings()
    if args.action == 'prepare':
        print(budget.prepare(root, root.parent/'g3-budget-registration-a'))
    else:
        follow(root,args.after_resume)
