// Owns the model service for one already-allocated CPU job. No shared services.
import { spawn } from "node:child_process";
import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { startFixedQwen } from "./fixed-qwen-session.mjs";
const [run, slot] = process.argv.slice(2);
if (!run || !slot) throw Error("Run folder and allocated CPU slot are required");
const python = path.resolve("engine/.venv/Scripts/python.exe");
let service;
const execute = async args => {
  const child = spawn(python, ["-B", ...args], { windowsHide: true, stdio: "inherit" });
  const code = await new Promise((resolve, reject) => { child.once("exit", resolve); child.once("error", reject); });
  if (code !== 0) throw Error(`Owned CPU stage exited ${code}`);
};
try {
  service = await startFixedQwen();
  if (!service) throw Error("Pinned CPU model unavailable");
  await writeFile(path.join(run, "model-service.json"), JSON.stringify({ pid: service.pid, url: service.url, startedAt: new Date().toISOString() }));
  await execute(["scripts/engine-question-batteries.py", "--url", service.url, "--cpu-slot", slot,
    "--out", path.join(run, "admissions"), "--resume"]);
  await execute(["scripts/engine-art-refresh.py", "--url", service.url, "--run", run]);
} finally { await service?.stop(); }
