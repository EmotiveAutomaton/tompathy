"""Public aggregate receipts; benchmark records remain in ignored storage."""
import json
from datetime import UTC, datetime
from pathlib import Path

from .protocol import PROTOCOL, PROTOCOL_PIN, receipt

FILES = {"attention":"attention-stops-2026-11.json","ai-involvement":"ai-involvement-2026-11.json",
         "edit-reasons":"edit-reasons-2026-11.json","goals":"goals-motivation-pilot-2026-11.json"}


def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf8",newline="\n")
    temporary.replace(path)


def bind_run(directory, identity):
    """Refuse mixing saved observations from different data/implementation pins."""
    path = Path(directory)/"run-identity.json"
    if path.exists():
        if json.loads(path.read_text(encoding="utf8")) != identity:
            raise ValueError("Saved benchmark identity differs; use a fresh private run directory")
    elif path.parent.exists() and any(path.parent.iterdir()):
        raise ValueError("Unbound existing benchmark records; use a fresh private run directory")
    else:
        save_json(path,identity)


def initialize_receipts(directory):
    directory = Path(directory)
    for capability,name in FILES.items():
        path = directory/name
        if not path.exists():
            save_json(path,receipt(capability))
    path = directory/"back-half-protocol-2026-11.json"
    value = {"protocol":PROTOCOL,"sha256":PROTOCOL_PIN,"date":"2026-11-11","status":"registered before outcomes",
        "interpretations":{"fourThreads":"deferred under the packet's two-thread shared-host limit",
          "historicalChanges":"October 25 local edits are preserved; its task queue is superseded",
          "inputFormats":"normalized private bundle contract; actual EX exports need verified adapters",
          "aucUncertainty":"paired whole-writer bootstrap of fixed OOF forecasts",
          "V3":"mean of the two page-scaled readers", "A1":"population standard deviation of word nats",
          "tfidfTies":"candidate ID order", "alignment":"Unicode code-point word lengths, >=98% of both sequences; >5% session loss stops"}}
    if path.exists() and json.loads(path.read_text(encoding="utf8"))["sha256"] != PROTOCOL_PIN:
        raise ValueError("Do not replace a frozen protocol silently")
    save_json(path,value)


def scoreboard(directory, output):
    directory = Path(directory)
    lines = ["# Engine scoreboard", "", "Only measured engine accuracy belongs here. Pending rows are not zero scores.",
        "Field labels remain off. A passed software test is not a natural-writing result.", "",
        "| Capability | Benchmark | Units | Metric | Baseline | Engine | 95% interval | Bar | Date | Receipt |",
        "|---|---|---|---|---|---|---|---|---|---|"]
    for capability,name in FILES.items():
        value = json.loads((directory/name).read_text(encoding="utf8"))
        rows = value.get("rows",[]) or [{}]
        unit,metric = 'writers','mean within-writer AUC'
        if capability == 'edit-reasons':
            unit = 'edits'
            comparison = value.get('comparison',{})
            baseline = comparison.get('direct',{})
            engine = comparison.get('cascade',value.get('feature',{}))
            rows = [{"metric":m,"baseline":baseline.get(k),"engine":engine.get(k)} for k,m in
                (('macroF1','macro-F1'),('twoWayAccuracy','two-way accuracy'))] if engine else [{}]
            metric = 'macro-F1; two-way accuracy'
        elif capability == 'goals':
            unit,metric = 'documents / authors','top-1; MRR'
            pilot = value.get('pilot',{})
            if pilot.get('readers'):
                rows = [{"metric":f"departures minus {ref}: {m}",
                    "baseline":pilot['readers'][ref][k]['mean'],"engine":pilot['readers']['departures'][k]['mean'],
                    "interval":pilot['differences'][ref][k]['interval']} for ref in ('body','cues-only')
                    for k,m in (('top1','top-1'),('reciprocalRank','MRR'))]
        for row in rows:
            def number(key, row=row):
                val = row.get(key)
                return f"{val:.4f}" if type(val) in (int,float) else "—"
            interval = row.get("interval")
            ci = f"[{interval[0]:.4f}, {interval[1]:.4f}] (gain)" if interval else "—"
            bar = PROTOCOL[capability]["rows"].get(row.get('id','1'))
            label = capability + (" (pilot)" if capability == "goals" else "")
            if row.get('id'):
                label += ' · row '+row['id']
            lines.append(f"| {label} | {value['scope']} | {unit} | {row.get('metric',metric)} | {number('baseline')} | {number('engine')} | {ci} | {f'+{bar:.2f}' if bar is not None else ''} | {value.get('date','not run')} | [{row.get('status',value['status'])}](../engine/validation/{name}) |")
    lines += ["", "History contrasts and exploratory variants remain separately identified in each receipt.",
        "A CoAuthor involvement result applies to accepted suggestions from its 2021 model; it does not establish modern whole-document detection.", ""]
    Path(output).write_text("\n".join(lines),encoding="utf8",newline="\n")


def public_receipt(value):
    # Per-writer coverage is useful locally but hashed identities are still private.
    result = {k:v for k,v in value.items() if k != "countsByWriterGenre"}
    if "countsByWriterGenre" in value:
        result["writerGenreCells"] = len(value["countsByWriterGenre"])
        result["sentences"] = sum(r["sentences"] for r in value["countsByWriterGenre"])
    result["date"] = datetime.now(UTC).date().isoformat()
    return result
