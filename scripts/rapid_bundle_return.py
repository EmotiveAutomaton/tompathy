"""Verify and privately hand over TP72, then record only its constructed acceptance."""

import shutil
import sys
import uuid
from pathlib import Path

from rapid_card_record import RETURN, SCOREBOARD, STATUS, live_line
from rapid_cpu_dispatch import ROOT, confirmed
from rapid_land import PUBLIC, put
from rapid_later_record import write_text
from tompathy_engine.eval.evidence import append
from word_table_lane import now, pin, read, write

RECEIVER = Path("../SoundingLine/sounding-line").resolve()
RELATIVE = ".agent-state/drive-20261115/week8/TP72-delivery-a"
NOTE = Path("docs/exchange/result-sheets/TP72.md")
LEDGER = "E-TP72-PRODUCER-20261127"


def verify_private(folder, manifest, archive_pin, proof_pin):
    from tmp2.assemble72 import verified

    if {p.name for p in folder.iterdir()} != {
        "payload",
        "manifest.json",
        "producer-rehearsal.json",
    }:
        raise ValueError("Unexpected material in the recipient handoff")
    if (
        pin(folder / "manifest.json") != archive_pin
        or pin(folder / "producer-rehearsal.json") != proof_pin
    ):
        raise ValueError("Recipient manifest or rehearsal certificate differs")
    verified(folder / "payload", manifest)


def check_invented_complements():
    # Only the receiving gate code is imported; the example rosters are invented.
    path = RECEIVER / "runners/drive/sealed/week6-sm-science"
    sys.path[:0] = [str(path), str(RECEIVER / "runners/drive/cards"), str(RECEIVER)]
    from independent_release import Entry, decide

    known = frozenset(range(12))
    small = frozenset(range(11))
    entries = [
        (0, "all", [Entry({"n": 12}, known)]),
        (1, "subset", [Entry({"n": 11}, small)]),
    ]
    allowed, _ = decide(entries, known)
    if "all" not in allowed or "subset" in allowed:
        raise ValueError("Receiver did not suppress the invented one-person complement")
    return pin(path / "independent_release.py")


def handover(out):
    from tmp2.assemble72 import verified

    source = confirmed(out)
    record = read(out / "receipt.json")
    result = read(out / "producer-rehearsal.json")
    if record["card"] != "TP72-rehearsal" or record["result"] != result:
        raise ValueError("Rehearsal receipt does not bind this candidate")
    plans = ROOT / (out.name + "-registration.json")
    plan = read(plans)
    candidate = Path(plan["candidate"])
    h = pin(candidate / "manifest.json")
    if (
        source != read(out / "complete.json")["sourceReceiptPin"]
        or not result["inventedOnly"]
        or not result["matchingRanksExact"]
        or not result["receiverFiltersExercised"]
        or not all(
            result["receiverChecks"][k]
            for k in ("finiteSchemaAndSize", "originalFormatSyntheticConversation")
        )
        or h != result["manifestSha256"]
        or h != plan["manifestSha256"]
        or result["registeredPin"] != pin(plans)
        or result["setsPerFamily"] != 200
        or result["twoSpeakerRowsReleased"] != 0
        or len(result["tables"]["history"]) != 9
        or len(result["tables"]["conversation"]) != 2
    ):
        raise ValueError("A required producer rehearsal or source binding is missing")
    extra = check_invented_complements()
    manifest = read(candidate / "manifest.json")
    verified(candidate / "payload", manifest)
    location = RECEIVER / RELATIVE
    if location.resolve() != location or not location.is_relative_to(
        RECEIVER / ".agent-state"
    ):
        raise ValueError("Unexpected private handoff destination")
    location.parent.mkdir(parents=True, exist_ok=True)
    proof = out / "producer-rehearsal.json"
    if not location.exists():
        temp = location.parent / (".TP72-" + uuid.uuid4().hex)
        temp.mkdir()
        shutil.copytree(candidate / "payload", temp / "payload")
        shutil.copyfile(candidate / "manifest.json", temp / "manifest.json")
        shutil.copyfile(proof, temp / "producer-rehearsal.json")
        verify_private(temp, manifest, h, pin(proof))
        temp.rename(location)
    verify_private(location, manifest, h, pin(proof))
    receipt = {
        "at": now(),
        "destination": str(location),
        "sourceReceiptPin": source,
        "manifestSha256": h,
        "certificateSha256": pin(proof),
        "payloadFiles": len(manifest),
        "bytes": result["payloadBytes"],
        "inventedComplementGatePin": extra,
        "receiptStatus": "matched on recipient filesystem",
    }
    audit = ROOT / "TP72-delivery.json"
    if audit.exists():
        old = read(audit)
        if any(old[k] != v for k, v in receipt.items() if k != "at"):
            raise ValueError("A different private delivery already exists")
    else:
        put(audit, receipt)
    return result, read(audit)


def file_card(key, states, job=None):
    if key != "TP72":
        raise ValueError("Expected TP72")
    out = ROOT / (job or "TP72-rehearsal-a")
    result, audit = handover(out)
    source = audit["sourceReceiptPin"]
    public = PUBLIC / "readers-tp72-producer-2026-11.json"
    safe = {
        k: result[k]
        for k in (
            "manifestSha256",
            "payloadFiles",
            "payloadBytes",
            "priorTP58Manifest",
            "inventedOnly",
            "setsPerFamily",
            "draws",
            "historyAuthors",
            "deepAuthors",
            "twoSpeakerRowsReleased",
            "speechPeopleForDisclosureCheck",
            "missingTraitN",
            "largestSpeakerMeanDifference",
            "matchingRanksExact",
            "receiverFiltersExercised",
            "rotatedGramMatched",
            "receiverChecks",
            "tables",
            "size",
            "elapsedSeconds",
            "tokenizers",
        )
    }
    put(
        public,
        {
            **safe,
            "sourceReceiptPin": source,
            "ledger": LEDGER,
            "recipientCopyVerified": True,
            "certificateSha256": audit["certificateSha256"],
            "recipientComplementFixtureVerified": True,
            "recipientComplementGatePin": audit["inventedComplementGatePin"],
            "scope": "Invented producer rehearsal and byte-verified handover. Sealed acceptance and human results are separate.",
        },
    )
    brief = (
        f"Sounding Line received {result['payloadFiles']} verified payload files. Invented histories exercised all nine "
        "tables. The two-speaker fixture produced zero releasable rows, and a larger invented group exercised both conversation tables."
    )
    append(
        PUBLIC / "EVIDENCE_LEDGER.jsonl",
        {
            "id": LEDGER,
            "date": "2026-11-27",
            "family": "Round 37 sealed reader software",
            "claims": ["P5", "S3"],
            "question": "Does the frozen producer implement both sealed adapters and their matched controls?",
            "data": public.as_posix(),
            "estimate": {
                "sourceReceiptPin": source,
                "manifestSha256": safe["manifestSha256"],
                "historyTables": 9,
                "conversationTables": 2,
                "setsPerFamily": 200,
            },
            "interval": "Constructed software checks only.",
            "bar": "Real frozen passes on invented inputs, both control families, receiver disclosure checks and exact recipient file hashes.",
            "verdict": brief,
            "limit": "The recipient owns independent target-image rehearsal, access and any human-data results.",
        },
    )
    if LEDGER not in NOTE.read_text(encoding="utf8"):
        extra = (
            f"\n\n## Verified handover\n\n{brief} The private recipient directory is `{RELATIVE}/` in the Sounding Line checkout. "
            f"The SHA-256 of its `manifest.json` is `{audit['manifestSha256']}`. The producer certificate is "
            f"`producer-rehearsal.json`, SHA-256 `{audit['certificateSha256']}`. Each recipient file matched the source manifest. "
            f"On the invented two-speaker test, the largest discrepancy against averaging direct per-turn readings was {result['largestSpeakerMeanDifference']:.3g}. "
            "The receiver’s disclosure code also withheld an invented eleven-person subset within a twelve-person roster.\n\n"
            f"[Invented checks and source receipt · {LEDGER}](../../../engine/validation/{public.name})\n"
        )
        write_text(NOTE, NOTE.read_text(encoding="utf8").rstrip() + extra)
    for p, link in (
        (STATUS, NOTE.as_posix()),
        (SCOREBOARD, NOTE.relative_to("docs").as_posix()),
    ):
        t = p.read_text(encoding="utf8")
        if LEDGER not in t:
            first, rest = t.split("\n", 1)
            write_text(
                p,
                first
                + "\n\n**November 27 · TP72.** "
                + brief
                + f" [{LEDGER}]({link})\n\n"
                + rest.lstrip("\n"),
            )
    lines = RETURN.read_text(encoding="utf8").splitlines()
    lines[0] = live_line(states)
    i = next(i for i, l in enumerate(lines) if l.startswith("| TP72 ·"))
    lines[i] = (
        f"| TP72 · Sealed bundle v2 | {brief} | [TP72 · {LEDGER}](result-sheets/TP72.md) |"
    )
    write_text(RETURN, "\n".join(lines) + "\n")
    ans = {
        "public": public.as_posix(),
        "sha256": pin(public),
        "sourceReceiptPin": source,
    }
    write(ROOT / "TP72-landing.json", {**ans, "ledger": LEDGER})
    return ans
