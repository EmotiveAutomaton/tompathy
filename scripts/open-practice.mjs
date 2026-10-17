import { spawn } from "node:child_process";
import { mkdir, open, readFile } from "node:fs/promises";
import path from "node:path";
import { randomUUID } from "node:crypto";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const profile = process.argv[2] === "--profile" ? process.argv[3] : undefined;
await mkdir(path.join(root, ".local"), { recursive: true });
const receipt = path.join(
  root,
  ".local",
  `practice-launch-${randomUUID()}.json`,
);
const log = await open(receipt.replace(/\.json$/, ".log"), "a");
try {
  // The host owns its exact engine child until review Chrome closes. Detaching
  // from this short-lived command lets practice survive terminal/chat closure.
  const host = spawn(
    process.execPath,
    [
      path.join(root, "scripts/practice-host.mjs"),
      receipt,
      ...(profile ? [path.resolve(profile)] : []),
    ],
    {
      cwd: root,
      detached: true,
      windowsHide: true,
      stdio: ["ignore", log.fd, log.fd],
    },
  );
  let launchError;
  host.once("error", (e) => {
    launchError = e;
  });
  host.unref();
  const deadline = Date.now() + (process.env.TOMPATHY_CLEF === "1" ? 240000 : 90000);
  let result;
  while (!result && Date.now() < deadline) {
    if (launchError) throw launchError;
    try {
      result = JSON.parse(await readFile(receipt, "utf8"));
    } catch {}
    if (!result) await new Promise((resolve) => setTimeout(resolve, 200));
  }
  if (!result)
    throw Error(
      `Practice has not confirmed startup. Inspect ${receipt.replace(/\.json$/, ".log")}.`,
    );
  if (result.error) throw Error(result.error);
  console.log(
    `Live engine practice is ready in Chrome ${result.chromeVersion}.\nConnect the engine and enable Follow pages on the practice page. Open ToMpathy once; it follows new pages while its panel is open.\nThe local companion stays available until review Chrome closes. You can close this launcher.\nReceipt: ${receipt}`,
  );
} catch (error) {
  console.error(`Practice setup failed: ${error.message}`);
  process.exitCode = 1;
} finally {
  await log.close();
}
