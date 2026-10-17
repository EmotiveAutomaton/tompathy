import { writeFile } from "node:fs/promises";
import { startPractice } from "./practice-session.mjs";

const receipt = process.argv[2];
let session;
try {
  session = await startPractice({ profile: process.argv[3] });
  await writeFile(
    receipt,
    JSON.stringify(
      {
        startedAt: new Date().toISOString(),
        hostPid: process.pid,
        companionPid: session.server?.pid,
        reused: session.reused,
        chromeVersion: session.review.receipt.chromeVersion,
        url: session.url,
        implementation: session.implementation,
      },
      null,
      2,
    ),
  );
  if (session.reused) await session.review.browser.close();
  else {
    let stopping = false;
    const finish = async () => {
      if (stopping) return;
      stopping = true;
      await session.stop();
      await session.review.browser.close().catch(() => {});
    };
    process.once("SIGINT", () => void finish());
    process.once("SIGTERM", () => void finish());
    session.review.browser.once("disconnected", () => void finish());
    session.server.once("exit", () => void finish());
  }
} catch (error) {
  await session?.stop();
  await session?.review.browser.close().catch(() => {});
  await writeFile(receipt, JSON.stringify({ error: error.message }));
  process.exitCode = 1;
}
