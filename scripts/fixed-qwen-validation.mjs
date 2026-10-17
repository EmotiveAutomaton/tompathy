import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { writeFile } from "node:fs/promises";
import path from "node:path";
import { startFixedQwen } from "./fixed-qwen-session.mjs";

let session;
try {
  session = await startFixedQwen();
  if (!session) throw Error("Exact fixed Qwen is unavailable");
  const script = `import json, sys, time
from pathlib import Path
from tompathy_engine.preview.fixed_backend import FixedQwen
from tompathy_engine.preview.judgments import fixed_reader
from tompathy_engine.transcribe.cache import Cache
backend = FixedQwen(sys.argv[1])
reader = fixed_reader(backend, Cache(Path('.local/preview-score-cache/judgments.sqlite')))
start = time.monotonic()
def check():
    if time.monotonic() - start > 90: raise TimeoutError('Fixed reader timing bound')
try:
    with backend.checking(check):
        result = reader.ask('Q1', context='The garden is quiet.', text='A bird sings in the garden.', admission_test=True)
    print(json.dumps({'pin': reader.pin, 'seconds': time.monotonic()-start, 'answer': result['answer'], 'passed': True, 'scope': 'one constructed software smoke; no new scientific admission'}))
finally:
    backend.close()
`;
  const { stdout } = await promisify(execFile)(path.resolve("engine/.venv/Scripts/python.exe"), ["-c", script, session.url], { windowsHide: true, timeout: 120000, env: { ...process.env, OMP_NUM_THREADS: "1", OPENBLAS_NUM_THREADS: "1" } });
  const result = JSON.parse(stdout);
  await writeFile("evidence/fixed-qwen-validation.json", JSON.stringify({ checkedAt: new Date().toISOString(), ...result }, null, 2));
  console.log(JSON.stringify(result));
} finally { await session?.stop(); }
