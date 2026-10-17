// Focused recheck of the real news capture that exposed invalid root-cue IDs.
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import path from "node:path";
import { startFixedQwen } from "./fixed-qwen-session.mjs";

let service;
try {
  service = await startFixedQwen();
  if (!service) throw Error("Exact fixed Qwen reader is unavailable");
  const script = `import json, sys, time
from pathlib import Path
from datetime import datetime, UTC
from tompathy_engine.packet.build import build_packet
from tompathy_engine.packet.contract import Packet
from tompathy_engine.preview.build import build_preview
from tompathy_engine.preview.fixed_backend import FixedQwen
from tompathy_engine.preview.judgments import goals
from tompathy_engine.transcribe.cache import Cache
capture = json.loads(Path('.local/preview-live-news.json').read_text(encoding='utf8'))
packet = build_preview(build_packet(capture))
module = next(m for m in packet['preview']['modules'] if m['id'] == 'goals')
module['status'] = 'running'
backend = FixedQwen(sys.argv[1])
start = time.monotonic()
def check():
    if time.monotonic() - start > 180: raise TimeoutError('Focused goal recheck budget')
def publish():
    Packet.model_validate(packet)
report = {'checkedAt': datetime.now(UTC).isoformat(), 'source': capture['source'], 'revision': capture['revision'], 'scope': 'Focused real-model goal recheck; not a full live-page timing or scientific admission'}
try:
    goals(backend, Cache(Path('.local/preview-score-cache/judgments.sqlite')))(packet, check, publish)
    module['status'] = 'complete'
except TimeoutError:
    module['status'] = 'skipped'
finally:
    report.update(seconds=time.monotonic()-start, status=module['status'], goalNodes=len(packet.get('goalHierarchy', {}).get('nodes', [])), governingCover=any(n.get('level') == 'document' for n in packet.get('goalHierarchy', {}).get('nodes', [])))
    report['passed'] = report['goalNodes'] > 0 and module['status'] in ('complete', 'skipped')
    Path('evidence/preview-goal-recheck.json').write_text(json.dumps(report, indent=2)+'\\n', encoding='utf8')
    Path('.local/preview-goal-recheck-packet.json').write_text(json.dumps(packet), encoding='utf8')
    backend.close()
    print(json.dumps(report), flush=True)
if not report['passed']: raise RuntimeError('No valid goal output')
`;
  const { stdout } = await promisify(execFile)(path.resolve("engine/.venv/Scripts/python.exe"), ["-c", script, service.url], {
    windowsHide: true, timeout: 210000, env: { ...process.env, OPENBLAS_NUM_THREADS: "1", OMP_NUM_THREADS: "1" },
  });
  console.log(stdout.trim());
} finally { await service?.stop(); }
