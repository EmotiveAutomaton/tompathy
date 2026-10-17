import { access, readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { spawn, execFile } from "node:child_process";
import { promisify } from "node:util";
import { createServer } from "node:net";
import path from "node:path";
import os from "node:os";

const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
export async function startFixedQwen({ log = console.log } = {}) {
  const binary = process.env.TOMPATHY_OLLAMA ?? path.join(process.env.LOCALAPPDATA ?? "", "Programs/Ollama/ollama.exe");
  const models = process.env.TOMPATHY_OLLAMA_MODELS ?? path.resolve("../LocalLM/ollama_models");
  const manifest = path.join(models, "manifests/registry.ollama.ai/library/qwen3.5/9b");
  try { await access(binary); await access(manifest); } catch {
    log("Fixed Qwen unavailable: install the exact local runtime/model or set TOMPATHY_OLLAMA and TOMPATHY_OLLAMA_MODELS. No weights are downloaded.");
    return null;
  }
  const digest = createHash("sha256").update(await readFile(manifest)).digest("hex");
  if (digest !== "6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7") {
    log("Fixed Qwen unavailable: local model digest differs from the constructed receipt.");
    return null;
  }
  const socket = createServer();
  await new Promise((resolve, reject) => { socket.once("error", reject); socket.listen(0, "127.0.0.1", resolve); });
  const url = `http://127.0.0.1:${socket.address().port}`;
  await new Promise(resolve => socket.close(resolve));
  const child = spawn(binary, ["serve"], { windowsHide: true, stdio: ["ignore", "ignore", "pipe"], env: {
    ...process.env, OLLAMA_HOST: url, OLLAMA_MODELS: models,
    OLLAMA_NUM_PARALLEL: "1", OLLAMA_MAX_LOADED_MODELS: "1", OLLAMA_KEEP_ALIVE: "120",
    CUDA_VISIBLE_DEVICES: "-1", HIP_VISIBLE_DEVICES: "-1", ROCR_VISIBLE_DEVICES: "-1",
  }});
  let tail = "", failure;
  if (child.pid) {
    try { os.setPriority(child.pid, os.constants.priority.PRIORITY_BELOW_NORMAL); }
    catch (error) { failure = Error(`Could not lower owned reader priority: ${error.message}`); }
  }
  child.stderr.on("data", data => { tail = (tail + data).slice(-2000); });
  child.on("error", error => { failure = error; });
  const stop = async () => {
    if (child.exitCode === null && child.pid && !child.killed) {
      const ended = new Promise(resolve => child.once("exit", resolve));
      // Exact child created above, including only its own model-runner children.
      if (process.platform === "win32") await promisify(execFile)("taskkill", ["/PID", String(child.pid), "/T", "/F"], { windowsHide: true }).catch(error => {
        if (child.exitCode === null) throw error;
      });
      else child.kill();
      await Promise.race([ended, delay(5000)]);
      if (child.exitCode === null && child.signalCode === null) throw Error("Owned Qwen service did not confirm shutdown");
    }
  };
  try {
    const deadline = Date.now() + 10000;
    while (Date.now() < deadline) {
      if (failure || child.exitCode !== null) throw failure ?? Error(tail);
      let response;
      try { response = await fetch(url + "/api/version", { signal: AbortSignal.timeout(700), redirect: "error" }); } catch {}
      if (response?.ok) {
        if ((await response.json()).version !== "0.40.3") throw Error("Dedicated Ollama runtime differs from the constructed receipt.");
        log("Dedicated fixed Qwen service ready; CPU only, model loaded on first judgment.");
        return { url, stop, pid: child.pid };
      }
      await delay(150);
    }
    throw Error("Dedicated Qwen service did not become ready.");
  } catch (error) { await stop(); log(`Fixed Qwen unavailable: ${error.message}`); return null; }
}
