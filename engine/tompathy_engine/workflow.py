"""Explicit bounded history -> transcription -> fit -> reading workflow."""

import time
from datetime import datetime
from pathlib import Path

from .adapters.capture import validate_capture
from .adapters.history import ingest_history
from .adapters.wiki import fetch_history
from .admission import implementation_hash
from .features.records import transcribe
from .ledger.ids import canonical, digest
from .ledger.store import Ledger
from .models.pipeline import fit_pipeline
from .packet.build import build_packet


def immutable_write(path, value):
    data = canonical(value) + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError("A pinned history artifact cannot be overwritten")
        return
    with path.open("xb") as stream:
        stream.write(data)


def analyze_history(
    capture,
    *,
    directory,
    admissions,
    reader=None,
    questions=(),
    limit=20,
    maximum_calls=500,
    payload=None,
    adapter="wikipedia",
    progress=lambda _: None,
    cancel=lambda: False,
    fetcher=fetch_history,
):
    capture = validate_capture(capture)
    start = time.monotonic()

    def phase(message):
        if cancel():
            raise InterruptedError("History analysis cancelled")
        progress(message)

    phase("Fetching bounded revision history")
    if payload is None:
        if adapter != "wikipedia":
            raise ValueError(
                "Live fetch supports Wikipedia; Git needs an explicit normalized export"
            )
        payload = fetcher(capture["source"], artifact_id=capture["id"], limit=limit, cancel=cancel)
    if payload["artifact_id"] != capture["id"] or payload["source_uri"] != capture["source"]:
        raise ValueError("History source differs from the exact capture")
    # Every refresh gets a content-addressed immutable snapshot. Prior source
    # records and fitted models remain available; no artifact index is overwritten.
    folder = Path(directory) / digest(capture["id"]) / digest(payload)
    ledger = Ledger(folder / "ledger")
    phase("Compiling witnessed revisions and corrections")
    receipt = ingest_history(payload, ledger, adapter=adapter)
    immutable_write(folder / "source.json", payload)
    cutoff = datetime.fromisoformat(capture["capturedAt"])
    run = (
        folder
        / "runs"
        / digest(
            [
                implementation_hash(),
                reader.pin if reader else None,
                list(questions),
                capture,
                maximum_calls,
            ]
        )
    )
    model, labels = None, None
    if reader:
        phase("Transcribing admitted literal questions")
        requested = list(dict.fromkeys(["Q8", "Q9", *questions]))
        labels = transcribe(
            ledger.snapshot(),
            reader,
            domain="writing",
            until=cutoff,
            questions=requested,
            maximum=maximum_calls,
            progress=phase,
        )
        immutable_write(run / "labels.json", labels.model_dump(mode="json"))
        from .models.pipeline import cases

        options, corrections, _, _ = cases(
            ledger.snapshot(), domain="writing", until=cutoff, labels=labels, questions=questions
        )
        if options or corrections:
            phase("Fitting observed comparisons")
            model = fit_pipeline(
                ledger,
                population="writing-v0",
                until=cutoff,
                labels=labels,
                questions=questions,
                progress=phase,
            )
            immutable_write(run / "model.json", model.model_dump(mode="json"))
    phase("Building exact-capture reading")
    packet = build_packet(capture, ledger=ledger, model=model, admissions=admissions)
    receipt = {
        **receipt,
        "seconds": time.monotonic() - start,
        "snapshot": str(folder),
        "run": str(run),
        "fit_created": model is not None,
        "transcription_ran": labels is not None,
        "inferred_hypotheses": sum(h["status"] == "hypothesis" for h in packet["hypotheses"]),
        "scientific_acceptance": "requires external module admissions",
    }
    phase("History reading validated")
    return packet, receipt
