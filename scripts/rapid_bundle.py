"""Counted TP72 producer acceptance using only invented data, before private delivery."""

import importlib.util
import sys
import time
from pathlib import Path

from word_table_lane import pin, read, write

ROOT = Path(".local/rapid-20261127")
SL = Path("../SoundingLine/sounding-line").resolve()


def prepare(out, check):
    plan = read(ROOT / (out.name + "-registration.json"))
    candidate = Path(plan["candidate"])
    digest = pin(candidate / "manifest.json")
    if digest != plan["manifestSha256"]:
        raise ValueError("Candidate manifest differs")
    gate_path = SL / "runners/drive/sealed/week7_tmp1_shell.py"
    conversation_path = SL / "runners/drive/sealed/week8_tmp3_receiver.py"
    if (
        pin(gate_path) != plan["gatePin"]
        or pin(conversation_path) != plan["speakerAdapterPin"]
    ):
        raise ValueError("Receiver projection or disclosure validator changed")
    spec = importlib.util.spec_from_file_location("receiver_gate", gate_path)
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    payload = candidate / "payload"
    manifest = read(candidate / "manifest.json")
    gate.verify_bundle(payload, manifest)
    sys.dont_write_bytecode = True
    sys.path[:0] = [str(payload.resolve()), str(SL)]
    from run72 import offline

    sys.addaudithook(offline)
    if sys.platform == "win32":
        # On Windows, NumPy's architecture check otherwise asks for the host name.
        # Fill Python's platform cache with an empty node, under the same socket guard.
        import platform
        from unittest.mock import patch

        with patch.object(platform, "_node", return_value=""):
            platform.machine()
    if "retryDeadlineUTC" in plan:
        from datetime import datetime

        original_check = check
        deadline = datetime.fromisoformat(plan["retryDeadlineUTC"]).timestamp()

        def check():
            original_check()
            if time.time() >= deadline or (ROOT / "TP72-rehearsal-a/STOP").exists():
                raise RuntimeError("Original rehearsal deadline or STOP")

    check()
    import tokenizers
    from conversation import conversation, speaker_vectors
    from panels import CONVERSATION, HISTORY, Frozen, contracts
    from rehearse72 import exercise
    from runners.drive.sealed.week8_tmp3_receiver import project

    if tokenizers.__version__ != "0.22.2":
        raise ValueError("Tokenizer runtime differs")
    start = time.monotonic()
    work = out / "invented"
    last = [0.0]

    def checked():
        check()
        tick = time.monotonic()
        if tick - last[0] > 8:
            from word_table_lane import now

            write(
                out / "heartbeat.json",
                {"at": now(), "elapsedSeconds": tick - start, "scope": "invented only"},
            )
            last[0] = tick

    result = exercise(work, checked)
    gate.check_tables(work / "history", contracts(HISTORY))
    gate.check_tables(work / "conversation", contracts(CONVERSATION))
    # Use the receiving repository's actual adapter on invented original-format rows.
    surveys = [
        {
            "conversation_id": "made",
            "user_id": a,
            "partner_id": b,
            "how_enjoyable": n,
            "affect": 4,
            "my_extraversion": n,
            "your_extraversion": k,
        }
        for a, b, n, k in (("a", "b", 2, 1), ("b", "a", 3, 4))
    ]
    turns = [
        {"conversation_id": "made", "turn_id": i, "speaker": a, "utterance": t}
        for i, a, t in [
            (4, "edge", "end"),
            (2, "b", "An invented reply."),
            (1, "a", "One invented opening."),
            (3, "a", "The last invented turn."),
            (0, "edge", "start"),
        ]
    ]
    speakers, oskip = project(surveys, turns)
    if (
        oskip
        or len(speakers) != 2
        or speakers[0].outcomes["partner_extraversion"] != 4
        or len(speakers[0].turns) != 2
    ):
        raise ValueError(
            "Receiver agreement on speaker order or reciprocal rating failed"
        )
    frozen = Frozen()
    matched = speaker_vectors(speakers, frozen, checked)
    if matched["a"][0][2] != 2 or matched["b"][0][2] != 1:
        raise ValueError("Producer did not consume the two ordered receiver speakers")
    if conversation(speakers, work / "receiver-two", frozen, checked) or list(
        (work / "receiver-two").iterdir()
    ):
        raise ValueError(
            "Original-format two-speaker fixture should suppress all aggregates"
        )
    result.update(
        manifestSha256=digest,
        registeredPin=pin(ROOT / (out.name + "-registration.json")),
        payloadFiles=len(manifest),
        payloadBytes=sum((payload / p).stat().st_size for p in manifest),
        priorTP58Manifest=plan["originalTP58Manifest"],
        tokenizers=tokenizers.__version__,
        receiverChecks={
            "gatePin": plan["gatePin"],
            "speakerAdapterPin": plan["speakerAdapterPin"],
            "finiteSchemaAndSize": True,
            "originalFormatSyntheticConversation": True,
        },
        elapsedSeconds=time.monotonic() - start,
    )
    write(out / "producer-rehearsal.json", result)
    return result
