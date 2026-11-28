"""DU verified original prefixes and DV append-only workstation continuations."""

import ctypes
import hashlib
import json
import sys
import time

import rapid_gpu as gpu
import word_table_lane as lane

FLOOR = "Available commit reached the 8 GiB floor"


def scan(folder, items, kind, first=0, check=lambda: None):
    """Bind every durable ordinal, including invalid answers and the last short interval."""
    parse = gpu.marks.template(kind)[2]
    files, valid, counts = {}, 0, {}
    for index, path in enumerate(sorted(folder.glob("from-*.json")), first):
        if index % 256 == 0:
            check()
        if index >= len(items) or path.name != f"from-{index:06}.json":
            raise ValueError(
                "Saved reader rows contain a gap, duplicate or extra ordinal"
            )
        raw = path.read_bytes()
        batch = json.loads(raw)
        if len(batch) != 1 or batch[0]["id"] != items[index]["id"]:
            raise ValueError("Saved reply does not match the original ordered roster")
        row = batch[0]
        try:
            parsed = parse(json.loads(row["response"]))
        except (TypeError, ValueError):
            parsed = None
        if row["values"] != parsed:
            raise ValueError("Stored reply and parsed value differ")
        files[path.name] = hashlib.sha256(raw).hexdigest()
        valid += int(parsed is not None)
        if kind == "standing":
            group = "ed" if index < 24850 else "envent" if index < 31450 else "go"
            cell = counts.setdefault(group, {"rows": 0, "valid": 0})
            cell["rows"] += 1
            cell["valid"] += int(parsed is not None)
    return {
        "firstOrdinal": first,
        "nextOrdinal": first + len(files),
        "valid": valid,
        "sources": counts,
        "files": files,
    }


def original(old, job, cfg):
    out = old / "jobs" / job
    frozen = cfg["originals"][job]
    for name in ("released.json", "failed.json", "owner.json"):
        gpu.require_pin(out / name, frozen[name])
    owner = lane.read(out / "owner.json")
    fail, release = lane.read(out / "failed.json"), lane.read(out / "released.json")
    if (
        owner != fail["owner"]
        or owner != release["owner"]
        or owner["job"] != job
        or owner["registration"] != frozen["registration"]
        or fail["error"] != FLOOR
        or release["exitCode"] == 0
        or not release["childWaited"]
        or not release["sharedLeaseReacquired"]
    ):
        raise ValueError("Source is not an exactly released memory-floor stop")
    # OS creation ticks distinguish exit from PID reuse.
    from runners.stage9.process_identity import native_identity

    native = native_identity(owner["pid"])
    if native and native["created_ticks"] == owner["createdTicks"]:
        raise ValueError("The source process is still running")
    config = (
        "Q29-registration.json"
        if job == "G13-Q29"
        else "Q31-registration.json"
        if job == "G13-Q31"
        else "registration.json"
    )
    gpu.require_pin(old / config, owner["registration"])
    return lane.read(old / config)


def commit_partition(repo, root):
    import psutil
    from runners.drive.cards.week5_policy_v2 import lease_paths
    from runners.stage9.process_identity import native_identity

    class Performance(ctypes.Structure):
        _fields_ = (
            [("cb", ctypes.c_ulong)]
            + [
                (k, ctypes.c_size_t)
                for k in (
                    "commit",
                    "limit",
                    "peak",
                    "physical",
                    "available",
                    "cache",
                    "kernel",
                    "paged",
                    "nonpaged",
                    "pageSize",
                )
            ]
            + [(k, ctypes.c_ulong) for k in ("handles", "processes", "threads")]
        )

    p = Performance()
    if not ctypes.windll.psapi.GetPerformanceInfo(ctypes.byref(p), ctypes.sizeof(p)):
        raise OSError("Cannot measure system committed bytes")
    processes = {}

    def add(proc):
        for child in [proc, *proc.children(recursive=True)]:
            try:
                processes[child.pid, child.create_time()] = child.memory_info().private
            except psutil.NoSuchProcess:
                pass

    add(psutil.Process())
    supervisor = lane.read(root / "workstation-dispatcher.json")
    identity = native_identity(supervisor["pid"])
    if identity and identity["created_ticks"] == supervisor["createdTicks"]:
        add(psutil.Process(supervisor["pid"]))
    for file in lease_paths():
        try:
            native = lane.read(file)["native"]
        except FileNotFoundError:
            continue
        pid = native.get("pid", native.get("windows_pid"))
        if native_identity(pid) == native:
            try:
                add(psutil.Process(pid))
            except psutil.NoSuchProcess:
                pass
    own = sum(processes.values())
    total = p.commit * p.pageSize
    if not 0 <= own <= total:
        raise ValueError("Invalid system commit partition")
    return {
        "programAndSlotCommitGiB": own / 2**30,
        "otherCommitGiB": (total - own) / 2**30,
        "outsideFraction": (total - own) / total,
    }


def workstation(root, old, job, out, guard, thermal, cfg):
    from day_gpu import check, need_rows

    repo = old.parent.parent
    sys.path.insert(0, str(repo.parent / "SoundingLine/sounding-line"))

    def control():
        thermal.check()
        check(root, old)
        if (out / "STOP").exists():
            raise RuntimeError("Owner STOP")

    manifest = lane.read(old / "inputs/inputs.json")

    def arms():
        if job in {"G12r", "G14r"}:
            previous = job[:-1]
            src = original(old, previous, cfg)
            if src["inputManifest"] != cfg["inputs"]:
                raise ValueError("Original input manifest differs")
            yield (
                previous,
                "W",
                "standing" if job == "G12r" else "features",
                gpu.roster(old, manifest, previous),
            )
        elif job == "G16":
            ed, events = need_rows(old, manifest)
            yield None, "W", "need", ed + events
        else:
            import tp31_teacher as teacher
            from rapid_blog_gpu import calendar
            from rapid_sentences import prepare

            cfg29 = original(old, "G13-Q29", cfg)
            rows, _, census = prepare(
                old, old.parent / "person-teacher/cb/isear.json", teacher.sentences
            )
            if census != cfg29["sentences"]:
                raise ValueError("Q29 sentence roster differs")
            yield "G13-Q29", "W", "sentence", rows
            cfg31 = original(old, "G13-Q31", cfg)
            selection = old / "Q31-selection.json"
            gpu.require_pin(selection, cfg31["selectionPin"])
            loss, rows, census = calendar(
                lane.read(selection),
                old.parent / "week-20261122/Q20-inputs-a/spark-inputs",
                teacher.sentences,
                control,
            )
            if census != cfg31["roster"]:
                raise ValueError("Q31 blog roster differs")
            yield "G13-Q31", "sentence", "sentence", rows
            # The stopped job had not yet opened its loss arm.
            if (old / "jobs/G13-Q31/loss").exists():
                raise ValueError("Unexpected source loss arm needs binding")
            yield None, "loss", "loss", loss

    summaries = {}
    for previous, arm, kind, items in arms():
        control()
        base = {"nextOrdinal": 0, "valid": 0}
        if previous:
            source = old / "jobs" / previous / arm
            gpu.require_pin(
                source / "protocol.json", cfg["originals"][previous]["protocol"]
            )
            protocol = lane.read(source / "protocol.json")
            if (
                protocol["inputPin"]
                != gpu.marks.digest("\n".join(r["id"] for r in items))
                or protocol["modelPin"] != lane.W[1]
                or protocol["model"] != lane.W[0]
                or protocol["width"] != 1
                or protocol["think"]
                or protocol["options"]
                != {
                    "num_ctx": 4096,
                    "num_predict": 256,
                    "num_thread": 2,
                    "temperature": 0,
                    "seed": 23,
                }
                or any(protocol[k] != v for k, v in gpu.marks.protocol(kind).items())
            ):
                raise ValueError("Ordered inputs, model or prompt changed")
            base = scan(source, items, kind, check=control)
            lane.write(
                out / (arm + "-prefix.json"),
                {
                    **base,
                    "job": previous,
                    "original": cfg["originals"][previous],
                    "protocolPin": lane.pin(source / "protocol.json"),
                },
            )
        folder = out / arm
        pos = base["nextOrdinal"]
        model_size = lane.read(old / "jobs/G12/W/first100.json")["residentBytes"]
        while pos < len(items):
            try:
                gpu.reader_arm(
                    out,
                    items,
                    "W",
                    kind,
                    1,
                    guard,
                    job,
                    arm,
                    len(items) - base["nextOrdinal"],
                    start_at=pos,
                )
                break
            except lane.Pause as exc:
                if str(exc) != FLOOR:
                    raise
                progress = out / "progress.json"
                if progress.exists():
                    model_size = lane.read(progress)["residentBytes"]

                def event(state, arm=arm, model_size=model_size):
                    lane.append(
                        root / "workstation-memory.jsonl",
                        {
                            "at": lane.now(),
                            "job": job,
                            "arm": arm,
                            "state": state,
                            "availableGiB": lane.commit_free_gib(),
                            "residentGiB": model_size / 2**30,
                            **commit_partition(repo, root),
                        },
                    )

                event("pause")
                while True:
                    control()
                    time.sleep(60)
                    control()
                    if lane.commit_free_gib() > 8 + model_size / 2**30:
                        break
                event("resume")
                pos = scan(folder, items, kind, base["nextOrdinal"], control)[
                    "nextOrdinal"
                ]
        suffix = scan(folder, items, kind, base["nextOrdinal"], control)
        if suffix["nextOrdinal"] != len(items):
            raise ValueError("The joined ledger is incomplete")
        summaries[arm] = {
            "job": job,
            "prefixRows": base["nextOrdinal"],
            "suffixRows": len(suffix["files"]),
            "rows": len(items),
            "valid": base["valid"] + suffix["valid"],
            "prefixValid": base["valid"],
        }
        lane.write(out / (arm + "-joined.json"), summaries[arm])
    return summaries
