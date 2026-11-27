"""Witness the native G12 exit and run the frozen G14 worker under the same GPU lease."""

import contextlib
import ctypes
import os
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path

import psutil

COMMIT = "d2a3ca95ca2bdf528d3355364aef42b3a381145a"
REG = "2aaa9e0fc722a48e40e854b61dddc9b9c2a03828233e2c0fc3175afdcffa7f6a"


class Process:
    """Keep the same process object across exit, including while its PID is reusable."""

    def __init__(self, pid, expected_ticks=None):
        dll = self.dll = ctypes.WinDLL("kernel32", use_last_error=True)
        dll.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        dll.OpenProcess.restype = wintypes.HANDLE
        dll.GetProcessTimes.argtypes = [wintypes.HANDLE] + [
            ctypes.POINTER(wintypes.FILETIME)
        ] * 4
        dll.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        dll.WaitForSingleObject.restype = wintypes.DWORD
        dll.GetExitCodeProcess.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(wintypes.DWORD),
        ]
        dll.CloseHandle.argtypes = [wintypes.HANDLE]
        self.handle = dll.OpenProcess(0x101000, False, pid)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            times = [wintypes.FILETIME() for _ in range(4)]
            if not dll.GetProcessTimes(self.handle, *[ctypes.byref(t) for t in times]):
                raise ctypes.WinError(ctypes.get_last_error())
            ticks = times[0].dwHighDateTime << 32 | times[0].dwLowDateTime
            if expected_ticks is not None and ticks != expected_ticks:
                raise ValueError("The recorded native creation time differs")
            self.owner = {"pid": pid, "createdTicks": ticks}
        except BaseException:
            self.close()
            raise

    def close(self):
        self.dll.CloseHandle(self.handle)

    def wait(self, check):
        while True:
            state = self.dll.WaitForSingleObject(self.handle, 60000)
            if state == 0:
                code = wintypes.DWORD()
                if not self.dll.GetExitCodeProcess(self.handle, ctypes.byref(code)):
                    raise ctypes.WinError(ctypes.get_last_error())
                return code.value
            if state != 258:
                raise ctypes.WinError(ctypes.get_last_error())
            check()


def run(root, *, after_memory_stop=False):
    if os.name != "nt":
        raise RuntimeError("The follow-up requires native Windows process handles")
    code = root / "code" / COMMIT
    sys.path.insert(0, str(code))
    import rapid_gpu as worker

    lane = worker.lane
    lane.settings()
    worker.require_pin(root / "registration.json", REG)
    for name, expected in lane.read(root / "registration.json")["code"].items():
        worker.require_pin(code / name, expected)
    control = root / (
        "workstation-G14-after-stop" if after_memory_stop else "workstation-follow"
    )
    control.mkdir(exist_ok=True)

    def check():
        worker.check_stop(root)

    def release(out, owner, status, wrapper):
        if (
            lane.read(out / "owner.json") != owner
            or owner["registration"] != REG
            or owner["commit"] != COMMIT
        ):
            raise ValueError("The terminal owner differs from the witnessed process")
        if status == 0:
            worker.require_pin(
                out / "receipt.json",
                lane.read(out / "complete.json")["sourceReceiptPin"],
            )
            receipt = lane.read(out / "receipt.json")
            if (
                receipt["owner"] != owner
                or receipt["status"] != "complete"
                or (out / "failed.json").exists()
            ):
                raise ValueError("Inconsistent completion state")
        elif lane.read(out / "failed.json")["owner"] != owner:
            raise ValueError("Inconsistent failure state")
        while True:
            try:
                with lane.lease(worker.lock_path(root)):
                    if (out / "released.json").exists():
                        raise ValueError("A release was already recorded")
                    lane.write(
                        out / "released.json",
                        {
                            "owner": owner,
                            "at": lane.now(),
                            "exitCode": status,
                            "nativeExited": True,
                            "childWaited": True,
                            "sharedLeaseReacquired": True,
                            "wrapper": wrapper,
                            "witnessedBy": lane.identity(),
                        },
                    )
                break
            except lane.Busy:
                check()
                time.sleep(15)
        if status:
            raise RuntimeError("The stopped worker is preserved: " + owner["job"])

    with lane.lease(control / "observer.lock"):
        g12 = root / "jobs/G12"
        owner = lane.read(g12 / "owner.json")
        dispatcher = lane.read(root / "workstation-dispatcher.json")
        if (
            owner["pid"],
            owner["createdTicks"],
            owner["job"],
            dispatcher["registration"],
        ) != (225660, 134402653573201159, "G12", REG):
            raise ValueError("Unexpected original worker")
        if after_memory_stop:
            worker.require_pin(
                g12 / "failed.json",
                "e9ac71cfc42a7c2c4ba4dc6089de6e9ed88dee3615e466c18efa4997be35a55c",
            )
            worker.require_pin(
                g12 / "released.json",
                "3c9a076db208904301a3165b2184b296acdf85cc3aadca6bb4f90a72474785b6",
            )
            failure = lane.read(g12 / "failed.json")
            if (
                failure["owner"] != owner
                or failure["error"] != "Available commit reached the 8 GiB floor"
            ):
                raise ValueError("Expected the reviewed memory stop")
        elif not (g12 / "released.json").exists():
            with contextlib.ExitStack() as handles:

                def hold(pid, ticks=None):
                    proc = Process(pid, ticks)
                    handles.callback(proc.close)
                    return proc

                native = hold(owner["pid"], owner["createdTicks"])
                shim = hold(psutil.Process(owner["pid"]).ppid())
                parent = hold(dispatcher["pid"], dispatcher["createdTicks"])
                if psutil.Process(shim.owner["pid"]).ppid() != parent.owner["pid"]:
                    raise ValueError("Original dispatch chain differs")
                lane.write(
                    control / "watching.json",
                    {
                        "at": lane.now(),
                        "observer": lane.identity(),
                        "observerPin": lane.pin(Path(__file__)),
                        "native": owner,
                        "shim": shim.owner,
                        "parent": dispatcher,
                    },
                )
                status = native.wait(check)
                if shim.wait(check) != status:
                    raise RuntimeError("Venv launcher and native exit codes differ")
                parent_status = parent.wait(check)
                if parent_status and "Unexpected terminal identity" not in (
                    root / "workstation.err"
                ).read_text(errors="replace"):
                    raise RuntimeError("Unrecognized original dispatcher exit")
                release(g12, owner, status, shim.owner)
        prior = lane.read(g12 / "released.json")
        if (
            prior["owner"] != owner
            or prior["exitCode"] != (1 if after_memory_stop else 0)
            or not prior["childWaited"]
            or not prior["sharedLeaseReacquired"]
        ):
            raise ValueError("Cannot advance beyond G12")
        with lane.lease(root / "workstation-dispatch.lock"):
            out = root / "jobs/G14"
            if out.exists():
                raise ValueError("G14 needs a fresh output")
            while True:
                check()
                proc = subprocess.Popen(
                    [sys.executable, str(code / "rapid_gpu.py"), str(root), REG, "G14"]
                )
                while not (out / "owner.json").is_file() and proc.poll() is None:
                    time.sleep(1)
                if (out / "owner.json").is_file():
                    break
                if proc.wait() != 74 or out.exists():
                    raise RuntimeError("G14 did not acquire the GPU")
                time.sleep(15)
            g14 = lane.read(out / "owner.json")
            with contextlib.closing(Process(g14["pid"], g14["createdTicks"])) as native:
                if g14["job"] != "G14" or (
                    g14["pid"] != proc.pid
                    and psutil.Process(g14["pid"]).ppid() != proc.pid
                ):
                    raise ValueError("G14 does not belong to the new launcher")
                with contextlib.closing(Process(proc.pid)) as shim:
                    lane.write(
                        control / "watching-G14.json",
                        {"owner": g14, "wrapper": shim.owner, "at": lane.now()},
                    )
                    status = native.wait(check)
                    if proc.wait() != status:
                        raise ValueError("G14 native and launcher exits differ")
                    release(out, g14, status, shim.owner)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--after-memory-stop", action="store_true")
    args = parser.parse_args()
    run(args.root.resolve(), after_memory_stop=args.after_memory_stop)
