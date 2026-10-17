import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { mkdir, mkdtemp, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { expect } from "@playwright/test";
import { openReview } from "./chrome-review.mjs";

await mkdir(".local", { recursive: true });
const profile = await mkdtemp(path.resolve(".local/lifecycle-check-"));
const folder = path.join(profile, "tompathy-engine");
const receipt = { checkedAt: new Date().toISOString(), checks: [] };
let review;
const connection = async () => ({
  ...JSON.parse(await readFile(path.join(folder, "connection.json"), "utf8")),
  token: (await readFile(path.join(folder, "token"), "utf8")).trim(),
});
const healthy = async (c) => {
  try {
    return (
      (
        await fetch(c.url + "/v1/health", {
          headers: { Authorization: `Bearer ${c.token}` },
          signal: AbortSignal.timeout(1000),
        })
      ).status === 200
    );
  } catch {
    return false;
  }
};
const launch = async () => {
  await promisify(execFile)(
    process.execPath,
    ["scripts/open-practice.mjs", "--profile", profile],
    { cwd: process.cwd(), windowsHide: true, timeout: 60000 },
  );
  review = await openReview({ profile, showGuide: false });
  return review.browser
    .contexts()[0]
    .pages()
    .find((p) => p.url().endsWith("/practice.html"));
};
try {
  let guide = await launch();
  const first = await connection();
  expect(await healthy(first)).toBe(true);
  receipt.checks.push(
    "Startup command exited; detached companion remains healthy",
  );
  const settings = await review.browser.contexts()[0].newPage();
  await settings.goto("chrome://extensions/");
  await settings.evaluate(
    async (id) =>
      chrome.developerPrivate.addHostPermission(id, "http://127.0.0.1/*"),
    review.receipt.extensionId,
  );
  await settings.close();
  await guide.bringToFront();
  await guide.getByRole("button", { name: /Connect local engine/ }).click();
  await expect(guide.locator("#connection")).toContainText(
    "Connected to engine",
  );
  await review.cdp.send("Browser.close");
  await review.browser.close();
  review = undefined;
  await expect.poll(() => healthy(first), { timeout: 10000 }).toBe(false);
  receipt.checks.push(
    "Closing only the disposable review Chrome stops its companion",
  );
  guide = await launch();
  const second = await connection();
  expect(await healthy(second)).toBe(true);
  expect(second.token).not.toBe(first.token);
  const restored = await guide.evaluate(
    async () =>
      (await chrome.storage.local.get("tompathy-provider"))[
        "tompathy-provider"
      ],
  );
  expect(restored).toEqual({
    kind: "local",
    url: second.url,
    token: second.token,
  });
  receipt.checks.push(
    "Restart restores prior selected connection with a fresh token and live port",
  );
  receipt.passed = true;
} catch (error) {
  receipt.passed = false;
  receipt.failure = error.message;
  throw error;
} finally {
  if (review) {
    await review.cdp.send("Browser.close").catch(() => {});
    await review.browser.close().catch(() => {});
  }
  const last = await connection().catch(() => null);
  if (last)
    await expect.poll(() => healthy(last), { timeout: 10000 }).toBe(false);
  await mkdir("evidence", { recursive: true });
  await writeFile(
    "evidence/practice-lifecycle.json",
    JSON.stringify(receipt, null, 2),
  );
  console.log(JSON.stringify(receipt, null, 2));
}
