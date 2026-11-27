"""Continue the registered Spark queue after the pre-inference Q34 import failure."""

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("/home/agent/tompathy-open/rapid-20261127")
COMMIT = "d2a3ca95ca2bdf528d3355364aef42b3a381145a"
REG = "2aaa9e0fc722a48e40e854b61dddc9b9c2a03828233e2c0fc3175afdcffa7f6a"
Q26 = "3d8813a933033506d9c9d2ff8f1bb2e550b42a2e658530363be177c7c49e3132"
CODE = ROOT / "code" / COMMIT
sys.path.insert(0, str(CODE))
import rapid_gpu as worker
from word_table_lane import Busy, identity, lease, now, pin, read, write


def verify_exit(owner):
    if (
        owner["bootId"] != Path("/proc/sys/kernel/random/boot_id").read_text().strip()
        or owner["registration"] != REG
        or owner["commit"] != COMMIT
    ):
        raise ValueError("Owner registration or boot differs")
    p = Path("/proc") / str(owner["pid"]) / "stat"
    if p.exists() and p.read_text().rsplit(")", 1)[1].split()[19] == str(
        owner["startTicks"]
    ):
        raise ValueError("Original worker is still live")


def run():
    worker.lane.settings()
    worker.require_pin(ROOT / "registration.json", REG)
    for name, h in read(ROOT / "registration.json")["code"].items():
        worker.require_pin(CODE / name, h)
    prior = ROOT / "jobs/Q34"
    failure = read(prior / "failed.json")
    owner = read(prior / "owner.json")
    release = read(prior / "released.json")
    if (
        failure["error"] != "No module named 'scipy'"
        or release["owner"] != owner
        or release["exitCode"] != 1
        or not release["sharedLeaseReacquired"]
        or (prior / "first100.json").exists()
        or any(prior.glob("*.npz"))
    ):
        raise ValueError("Retry applies only to the original pre-inference failure")
    verify_exit(owner)
    worker.require_pin(ROOT / "jobs/Q26/receipt.json", Q26)
    if (
        read(ROOT / "jobs/Q26/complete.json")["sourceReceiptPin"] != Q26
        or worker.job_width(ROOT) != 1
    ):
        raise ValueError("Original measured width decision differs")
    env = dict(
        os.environ, PYTHONPATH=str(worker.WEEK / "deps"), PYTHONDONTWRITEBYTECODE="1"
    )
    subprocess.run(
        [
            sys.executable,
            "-c",
            "import scipy,torch,transformers; assert scipy.__version__=='1.18.1' and torch.cuda.is_available()",
        ],
        env=env,
        check=True,
    )
    retry = ROOT / "attempts/Q34-b"
    with lease(ROOT / "spark-dispatch.lock"):
        retry.mkdir(parents=True, exist_ok=False)
        # A STOP requested at either root is observed by the original worker.
        (retry / "STOP").symlink_to(ROOT / "STOP")
        (retry / "inputs").mkdir()
        shutil.copyfile(ROOT / "registration.json", retry / "registration.json")
        for name in ("inputs.json", "envent.jsonl.gz"):
            shutil.copyfile(ROOT / "inputs" / name, retry / "inputs" / name)
            worker.require_pin(retry / "inputs" / name, pin(ROOT / "inputs" / name))
        write(
            retry / "repair.json",
            {
                "priorOwner": owner,
                "priorFailurePin": pin(prior / "failed.json"),
                "priorReleasePin": pin(prior / "released.json"),
                "sourceRegistration": REG,
                "environment": "Original offline weekly SciPy 1.18.1 path",
                "supervisor": identity(),
                "supervisorPin": pin(Path(__file__)),
                "at": now(),
            },
        )
        for job in ("Q34", "Q27", "Q28", "Q32"):
            active = retry if job == "Q34" else ROOT
            out = active / "jobs" / job
            while True:
                worker.check_stop(ROOT)
                proc = subprocess.Popen(
                    [sys.executable, str(CODE / "rapid_gpu.py"), str(active), REG, job],
                    env=env,
                )
                code = proc.wait()
                if code == 74 and not out.exists():
                    time.sleep(15)
                else:
                    break
            owned = read(out / "owner.json")
            if owned["job"] != job or owned["pid"] != proc.pid:
                raise ValueError("Terminal identity differs")
            verify_exit(owned)
            while True:
                try:
                    with lease(worker.lock_path(ROOT)):
                        write(
                            out / "released.json",
                            {
                                "owner": owned,
                                "exitCode": code,
                                "childWaited": True,
                                "sharedLeaseReacquired": True,
                                "at": now(),
                            },
                        )
                    break
                except Busy:
                    worker.check_stop(ROOT)
                    time.sleep(5)
            if code:
                raise RuntimeError("Preserved stopped attempt for " + job)
            worker.require_pin(
                out / "receipt.json", read(out / "complete.json")["sourceReceiptPin"]
            )


if __name__ == "__main__":
    run()
