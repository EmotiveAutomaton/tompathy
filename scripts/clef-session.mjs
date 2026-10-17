import { access, readFile, rm } from "node:fs/promises";
import { spawn, execFile } from "node:child_process";
import { promisify } from "node:util";
import { randomUUID } from "node:crypto";
import path from "node:path";

const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
export async function startClef({ log = console.log } = {}) {
  const python = path.resolve(process.platform === "win32"
    ? ".local/clef-flash/venv/Scripts/python.exe" : ".local/clef-flash/venv/bin/python");
  await access(python);
  await access(".local/clef-flash/manifest.json");
  const config = path.resolve(`.local/clef-flash/session-${randomUUID()}.json`);
  const child = spawn(python, ["scripts/clef-local.py", "serve", "--config", config], {
    windowsHide: true, stdio: ["ignore", "pipe", "pipe"],
    env: { ...process.env, CUDA_VISIBLE_DEVICES: "-1", OMP_NUM_THREADS: "1", MKL_NUM_THREADS: "1" },
  });
  let tail = "", failure;
  child.on("error", error => { failure = error; });
  for (const stream of [child.stdout, child.stderr]) stream.on("data", data => {
    tail = (tail + data).slice(-4000);
  });
  const stop = async () => {
    if (child.exitCode === null && child.pid && !child.killed) {
      const ended = new Promise(resolve => child.once("exit", resolve));
      if (process.platform === "win32")
        await promisify(execFile)("taskkill", ["/PID", String(child.pid), "/T", "/F"], { windowsHide: true }).catch(error => {
          if (child.exitCode === null) throw error;
        });
      else child.kill();
      await Promise.race([ended, pause(5000)]);
      if (child.exitCode === null && child.signalCode === null) throw Error("Owned Clef process did not confirm shutdown");
    }
    await rm(config, { force: true });
  };
  try {
    log("Loading isolated Clef-flash on one CPU thread; reserving 16 GiB shared memory headroom.");
    const deadline = Date.now() + 180000;
    while (Date.now() < deadline) {
      if (failure || child.exitCode !== null) throw failure ?? Error(tail);
      let connection;
      try { connection = JSON.parse(await readFile(config, "utf8")); } catch {}
      if (connection) {
        const response = await fetch(connection.url + "/v1/health", {
          headers: { Authorization: `Bearer ${connection.token}` },
          signal: AbortSignal.timeout(2000), redirect: "error",
        });
        const health = await response.json();
        if (!response.ok || health.identity !== connection.identity) throw Error("Clef runtime pin mismatch");
        log(`Clef ready: CPU-only, ${health.loadSeconds.toFixed(1)}s model load, ${health.rssGiB.toFixed(1)} GiB resident.`);
        return { config, connection, health, stop, pid: child.pid };
      }
      await pause(250);
    }
    throw Error("Clef did not become ready within three minutes");
  } catch (error) { await stop(); throw error; }
}
