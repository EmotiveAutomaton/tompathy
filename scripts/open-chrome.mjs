import { access, mkdir } from "node:fs/promises";
import { spawn } from "node:child_process";
import path from "node:path";
import { verifyBuild } from "./check-build.mjs";
await verifyBuild();
const roots = [
  process.env.PROGRAMFILES,
  process.env["PROGRAMFILES(X86)"],
  process.env.LOCALAPPDATA,
].filter(Boolean);
let executable;
for (const root of roots) {
  const candidate = path.join(root, "Google/Chrome/Application/chrome.exe");
  try {
    await access(candidate);
    executable = candidate;
    break;
  } catch {}
}
if (!executable)
  throw Error(
    "Google Chrome was not found. Open Chrome yourself and load this project's dist folder.",
  );
const profile = path.resolve(".local/chrome-review");
await mkdir(profile, { recursive: true });
const child = spawn(
  executable,
  [
    `--user-data-dir=${profile}`,
    "--no-first-run",
    "--new-window",
    "chrome://extensions",
    "http://127.0.0.1:5173/testbed.html",
  ],
  { detached: true, stdio: "ignore", windowsHide: false },
);
child.unref();
console.log(
  `Opened ordinary Google Chrome with a separate development profile.\nLoad unpacked: ${path.resolve("dist")}\nChrome remembers this installation in the development profile. Pin ToMpathy, then use the testbed tab.\nNo extension sideloading flags or debugging ports were used.`,
);
