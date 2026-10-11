import { spawn } from "node:child_process";
import path from "node:path";
const url = "http://127.0.0.1:5173/testbed.html";
try {
  const response = await fetch(url, { signal: AbortSignal.timeout(1500) });
  if (
    response.ok &&
    (await response.text()).includes("ToMpathy · local testbed")
  ) {
    console.log(`Testbed is already running. Open ${url}`);
    process.exit(0);
  }
} catch {
  /* Start the project's server below. */
}
console.log(
  `Keep this terminal open. Testbed: ${url}\nInstalled Chrome extension: load ${path.resolve("dist")}\nUse npm run chrome to open a separate Chrome development profile.`,
);
const child = spawn(
  process.execPath,
  [
    "node_modules/vite/bin/vite.js",
    "--host",
    "127.0.0.1",
    "--port",
    "5173",
    "--strictPort",
  ],
  { stdio: "inherit" },
);
child.on("exit", (code) => process.exit(code ?? 1));
