// One owned model service at a time. Never touches shared research services.
import { spawn } from "node:child_process";
import path from "node:path";
import { startClef } from "./clef-session.mjs";
import { startFixedQwen } from "./fixed-qwen-session.mjs";

const mode = process.argv[2];
if (!["clef", "goals"].includes(mode)) throw Error("Choose clef or goals");
let service;
try {
  service = mode === "clef" ? await startClef() : await startFixedQwen();
  if (!service) throw Error("Exact model service unavailable");
  const child = spawn(path.resolve("engine/.venv/Scripts/python.exe"), [
    "scripts/preview-prepare-stage.py", mode,
    ...(mode === "clef" ? ["--config", service.config] : ["--url", service.url]),
    "--seconds", "1200",
  ], { windowsHide: true, stdio: "inherit" });
  const code = await new Promise((resolve, reject) => { child.once("exit", resolve); child.once("error", reject); });
  if (code !== 0) throw Error(`Preparation exited ${code}`);
} finally { await service?.stop(); }
