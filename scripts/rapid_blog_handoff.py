"""Arm the two Q31 blog readers when the source-bound selection is ready on the workstation."""

import argparse
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tarfile
import time
import uuid
from pathlib import Path

SPARK = "/home/agent/tompathy-open/rapid-20261127"
ENV = "/home/agent/venvs/engine/bin/python"
SNAPSHOT = "f235bb22bb413ffd9721ba074e118b8c49c86347"
PREVIOUS = "86477edf7ee5b3f26ed8dc79d14469522375fc36677cfa57946a64539b13ece7"
END = 1795968000
CODE = (
    "rapid_gpu.py",
    "rapid_marks.py",
    "rapid_worry.py",
    "week_spark.py",
    "word_table_lane.py",
    "spark-reader-job.py",
    "rapid_sentence_gpu.py",
    "rapid_sentences.py",
    "rapid_blog_gpu.py",
    "tp31_teacher.py",
)
TOOLS = ("rapid_after_gpu.py", "rapid_windows_follow.py")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def checked_file(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        if path.read_bytes() != payload:
            raise ValueError("An existing study input differs: " + path.name)
    else:
        with path.open("xb") as f:
            f.write(payload)


def selection(raw):
    d = json.loads(raw)
    if (
        set(d) != {"loss", "sample", "shards"}
        or not 1 <= len(d["loss"]) <= 6000
        or len(d["sample"]) != 10000
        or not d["shards"]
    ):
        raise ValueError("Unexpected blog selection schema or count")
    for k in ("loss", "sample"):
        if any(
            len(row) != 2
            or any(
                not isinstance(v, str) or not re.fullmatch(r"[0-9a-f]{64}", v)
                for v in row
            )
            for row in d[k]
        ):
            raise ValueError(
                "Only opaque task and opening keys may leave the source workstation"
            )
        if len({row[0] for row in d[k]}) != len(d[k]):
            raise ValueError("Duplicate registered inference key")
    if any(
        not re.fullmatch(r"[A-Za-z0-9._-]+\.jsonl\.gz", k)
        or not re.fullmatch(r"[0-9a-f]{64}", v)
        for k, v in d["shards"].items()
    ):
        raise ValueError("Invalid original shard manifest")


def assert_time(root):
    if (
        time.time() >= END
        or (root / "STOP").exists()
        or (root / "blog-setup/STOP").exists()
    ):
        raise RuntimeError("Owner STOP or end of the two-day packet")


def prepare_package(root):
    from rapid_cpu_dispatch import confirmed
    from rapid_sentence_register import register

    source = confirmed(root / "Q31-inputs-a")
    cfg = root / "Q31-registration.json"
    if not cfg.exists():
        register(root, SNAPSHOT, blog=True)
    raw = cfg.read_bytes()
    reg = json.loads(raw)
    if (
        reg["selectionReceiptPin"] != source
        or reg["commit"] != SNAPSHOT
        or set(reg["code"]) != set(CODE)
    ):
        raise ValueError("A different Q31 selection or snapshot is installed")
    plan = (root / "Q31-selection.json").read_bytes()
    selection(plan)
    if digest(plan) != reg["selectionPin"]:
        raise ValueError("Selected keys differ from their registered work")
    files = {"Q31-registration.json": raw, "Q31-selection.json": plan}
    for name in CODE:
        payload = (root / "code" / SNAPSHOT / name).read_bytes()
        if digest(payload) != reg["code"][name]:
            raise ValueError("Source snapshot changed")
        files["code/" + name] = payload
    for name in TOOLS:
        payload = subprocess.check_output(
            ["git", "show", SNAPSHOT + ":scripts/" + name]
        )
        checked_file(root / "tools" / SNAPSHOT / name, payload)
        files["tools/" + name] = payload
    dest = root / "blog-setup" / (digest(raw) + ".tar")
    if not dest.exists():
        with tarfile.open(dest, "x") as tar:
            for name, content in files.items():
                meta = tarfile.TarInfo(name)
                meta.size = len(content)
                meta.mode = 0o600
                tar.addfile(meta, io.BytesIO(content))
    h = digest(dest.read_bytes())
    if dest.stat().st_size > 32 * 1024 * 1024:
        raise ValueError("Blog dispatch package exceeds its reviewed limit")
    return dest, h, digest(raw)


def install_remote(root, archive_hash, reg_hash, upload):
    if (
        root != Path(SPARK)
        or not all(re.fullmatch("[a-f0-9]{64}", h) for h in (archive_hash, reg_hash))
        or not re.fullmatch("[0-9a-f]{32}", upload)
    ):
        raise ValueError("Invalid remote destination or binding")
    assert_time(root)
    file = root / ("Q31-inputs-" + upload + ".tar")
    if (
        file.stat().st_size > 32 * 1024 * 1024
        or digest(file.read_bytes()) != archive_hash
    ):
        raise ValueError("Transferred package differs")
    with tarfile.open(file, "r:") as tar:
        want = {
            "Q31-selection.json",
            "Q31-registration.json",
            *("code/" + n for n in CODE),
            *("tools/" + n for n in TOOLS),
        }
        entries = tar.getmembers()
        if (
            len(entries) != len(want)
            or {e.name for e in entries} != want
            or not all(e.isfile() for e in entries)
        ):
            raise ValueError("Package contents differ from the allowlist")
        data = {e.name: tar.extractfile(e).read() for e in entries}
    if digest(data["Q31-registration.json"]) != reg_hash:
        raise ValueError("Transferred registration differs")
    reg = json.loads(data["Q31-registration.json"])
    selection(data["Q31-selection.json"])
    if (
        reg["commit"] != SNAPSHOT
        or set(reg["code"]) != set(CODE)
        or digest(data["Q31-selection.json"]) != reg["selectionPin"]
    ):
        raise ValueError("Invalid remote selection or snapshot")
    for name in CODE:
        v = data["code/" + name]
        if digest(v) != reg["code"][name]:
            raise ValueError("Remote code binding differs")
        checked_file(root / "code" / SNAPSHOT / name, v)
    for name in TOOLS:
        checked_file(root / "tools" / SNAPSHOT / name, data["tools/" + name])
    for name in ("Q31-selection.json", "Q31-registration.json"):
        checked_file(root / name, data[name])
    return start_and_check(root, reg_hash, False)


def start_and_check(root, reg_hash, win):
    machine = "workstation" if win else "spark"
    previous = root / (machine + "-sentence-follow") / "armed.json"
    parent = json.loads(previous.read_bytes())
    if parent["registration"] != PREVIOUS:
        raise ValueError("Unrecognized parent GPU observer")
    control = root / (machine + "-blog-follow")
    control.mkdir(exist_ok=True)
    if (control / "stopped.json").exists():
        raise ValueError("Preserve the stopped blog supervisor")
    armed = control / "armed.json"
    proc = None
    if not armed.exists():
        assert_time(root)
        env = dict(
            os.environ,
            OPENBLAS_NUM_THREADS="2" if win else "4",
            MKL_NUM_THREADS="2" if win else "4",
            OMP_NUM_THREADS="2" if win else "4",
            PYTHONDONTWRITEBYTECODE="1",
        )
        if not win:
            env["PYTHONPATH"] = "/home/agent/tompathy-open/week-20261122/deps"
        with (control / "startup.log").open("xb") as log:
            proc = subprocess.Popen(
                [
                    sys.executable if win else ENV,
                    str((root / "tools" / SNAPSHOT / "rapid_after_gpu.py").resolve()),
                    str(root.resolve()),
                    "--blog-registration",
                    reg_hash,
                ],
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW
                | subprocess.BELOW_NORMAL_PRIORITY_CLASS
                if win
                else 0,
                start_new_session=not win,
            )
        until = time.monotonic() + 1200
        while not armed.exists():
            assert_time(root)
            if proc.poll() is not None or time.monotonic() > until:
                raise RuntimeError(
                    machine + " blog listener has no verified startup; inspect its log"
                )
            time.sleep(3)
    proof = json.loads(armed.read_bytes())
    if (
        proof["predecessor"] != parent["owner"]
        or proof["registration"] != reg_hash
        or proof["job"] != ("G13-Q31" if win else "Q31")
    ):
        raise ValueError("Unexpected blog listener identity")
    if win:
        from contextlib import closing

        from rapid_windows_follow import Process

        with closing(
            Process(proof["owner"]["pid"], proof["owner"]["createdTicks"])
        ) as p:
            if p.dll.WaitForSingleObject(p.handle, 0) != 258:
                raise ValueError("The registered Windows listener has exited")
    else:
        owner = proof["owner"]
        stat = (
            (Path("/proc") / str(owner["pid"]) / "stat")
            .read_text()
            .rsplit(")", 1)[1]
            .split()
        )
        if (
            Path("/proc/sys/kernel/random/boot_id").read_text().strip()
            != owner["bootId"]
            or stat[0] == "Z"
            or stat[19] != str(owner["startTicks"])
        ):
            raise ValueError("The registered Spark listener is absent")
    return proof


def wait_and_install(revision):
    from rapid_after_gpu import wait_predecessor
    from rapid_cpu_dispatch import ROOT, check, confirmed
    from word_table_lane import identity, lease, now, read, write

    root = ROOT.resolve()
    if not re.fullmatch(r"[a-f0-9]{40}", revision):
        raise ValueError("A committed installer is required")
    script = subprocess.check_output(
        ["git", "show", revision + ":scripts/rapid_blog_handoff.py"]
    )
    if script != Path(__file__).read_bytes().replace(b"\r\n", b"\n"):
        raise ValueError("The setup must match the committed installer")
    folder = root / "blog-setup"
    folder.mkdir(exist_ok=True)
    with lease(folder / "dispatcher.lock"):
        me = identity()
        try:
            parent = read(root / "sentence-card-queue/armed.json")
            if (
                parent["registration"]
                != "81074412082da07b5bb2144ce220cbe6d7781396cea21102bbfd5e3711aca336"
            ):
                raise ValueError("The input producer registration differs")
            write(
                folder / "armed.json",
                {
                    "owner": me,
                    "at": now(),
                    "predecessor": parent["owner"],
                    "code": revision,
                },
            )
            finished = root / "sentence-card-queue/complete.json"
            if not finished.exists():
                wait_predecessor(parent["owner"], check)
            done = read(finished)
            if done["owner"] != parent["owner"] or done["verified"][
                "Q31-inputs"
            ] != confirmed(root / "Q31-inputs-a"):
                raise ValueError("Unverified blog source completion")
            check()
            dest, h, reg = prepare_package(root)
            assert_time(root)
            ssh = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "spark"]
            errors = []
            try:
                windows = start_and_check(root, reg, True)
                write(folder / "workstation.json", windows)
            except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as e:
                errors.append("workstation: " + str(e))
            try:
                assert_time(root)
                upload = uuid.uuid4().hex
                subprocess.run(
                    [
                        "scp",
                        "-B",
                        str(dest),
                        "spark:" + SPARK + "/Q31-inputs-" + upload + ".tar",
                    ],
                    check=True,
                    timeout=180,
                )
                remote = json.loads(
                    subprocess.check_output(
                        [*ssh, ENV, "-", "--install", h, reg, upload],
                        input=script,
                        timeout=1300,
                    )
                )
                write(folder / "spark.json", remote)
            except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as e:
                errors.append("Spark: " + str(e))
            if errors:
                raise RuntimeError(". ".join(errors))
            write(
                folder / "complete.json",
                {
                    "owner": me,
                    "at": now(),
                    "spark": remote,
                    "workstation": windows,
                    "registration": reg,
                    "packagePin": h,
                    "sourceReceiptPin": done["verified"]["Q31-inputs"],
                },
            )
        except Exception as e:
            write(folder / "stopped.json", {"owner": me, "at": now(), "reason": str(e)})
            raise


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--await-selection", metavar="COMMIT")
    g.add_argument(
        "--install", nargs=3, metavar=("ARCHIVE_HASH", "REGISTRATION_HASH", "UPLOAD_ID")
    )
    args = p.parse_args()
    if args.install:
        print(json.dumps(install_remote(Path(SPARK), *args.install)))
    else:
        wait_and_install(args.await_selection)
