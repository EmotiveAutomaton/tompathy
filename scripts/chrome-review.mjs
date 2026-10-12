import { access, mkdir, readFile, writeFile, rm } from "node:fs/promises";
import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "@playwright/test";
import { verifyBuild } from "./check-build.mjs";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const pause = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const samePath = (a, b) =>
  process.platform === "win32"
    ? path.resolve(a).toLowerCase() === path.resolve(b).toLowerCase()
    : path.resolve(a) === path.resolve(b);

async function findChrome() {
  const candidates =
    process.platform === "win32"
      ? [
          process.env.PROGRAMFILES,
          process.env["PROGRAMFILES(X86)"],
          process.env.LOCALAPPDATA,
        ]
          .filter(Boolean)
          .map((folder) =>
            path.join(folder, "Google/Chrome/Application/chrome.exe"),
          )
      : process.platform === "darwin"
        ? ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
        : ["/usr/bin/google-chrome", "/usr/bin/google-chrome-stable"];
  for (const candidate of candidates) {
    try {
      await access(candidate);
      return candidate;
    } catch {}
  }
  throw Error(
    "Google Chrome was not found. Install Chrome, then run this launcher again.",
  );
}

async function connect(profile) {
  try {
    const [port, route] = (
      await readFile(path.join(profile, "DevToolsActivePort"), "utf8")
    )
      .trim()
      .split(/\r?\n/);
    if (!/^\d+$/.test(port) || !/^\/devtools\/browser\/[\w-]+$/.test(route))
      return null;
    // The browser UUID read from this profile prevents attaching to a reused port.
    const endpoint = `ws://127.0.0.1:${port}${route}`;
    const response = await fetch(`http://127.0.0.1:${port}/json/version`, {
      signal: AbortSignal.timeout(700),
    });
    const metadata = await response.json();
    if (new URL(metadata.webSocketDebuggerUrl).pathname !== route) return null;
    return await chromium.connectOverCDP(endpoint, { timeout: 2000 });
  } catch {
    return null;
  }
}

export async function openReview({
  profile = path.join(root, ".local/chrome-review"),
  showGuide = true,
} = {}) {
  process.chdir(root);
  const build = await verifyBuild();
  const info = JSON.parse(await readFile("dist/build-info.json", "utf8"));
  // All development state is confined to this checkout's own profiles.
  profile = path.resolve(profile);
  const localRoot = path.join(root, ".local") + path.sep;
  if (!profile.startsWith(localRoot))
    throw Error(
      "The review profile must be inside this project's .local directory.",
    );
  await mkdir(profile, { recursive: true });
  let browser = await connect(profile);
  let launchedProcess;
  const reusedBrowser = !!browser;
  if (!browser) {
    const executable = await findChrome();
    // A stopped Chrome can leave this file pointing at its old port. On
    // Windows a subsequent launch may not replace it. An existing live
    // connection above is preserved; a new launch must publish fresh metadata.
    await rm(path.join(profile, "DevToolsActivePort"), { force: true });
    const child = spawn(
      executable,
      [
        `--user-data-dir=${profile}`,
        "--remote-debugging-port=0",
        "--enable-unsafe-extension-debugging",
        "--no-first-run",
        "--no-default-browser-check",
        "--window-size=1440,1040",
        "about:blank",
      ],
      { detached: true, stdio: "ignore", windowsHide: false },
    );
    launchedProcess = child;
    let launchError;
    child.on("error", (error) => {
      launchError = error;
    });
    child.unref();
    const deadline = Date.now() + 15000;
    while (!browser && !launchError && Date.now() < deadline) {
      await pause(200);
      browser = await connect(profile);
    }
    if (launchError) throw launchError;
    if (!browser) {
      // This invocation owns this process. Do not leave a failed launch alive,
      // or touch another Chrome profile when installation cannot connect.
      if (child.exitCode === null) child.kill();
      throw Error(
        "The review Chrome profile did not connect. Close only its review windows and retry. Your regular Chrome windows can stay open.",
      );
    }
  }
  try {
    const cdp = await browser.newBrowserCDPSession();
    let installed;
    try {
      installed = (await cdp.send("Extensions.getExtensions")).extensions;
    } catch {
      throw Error(
        "This Chrome does not expose the required extension-development API. Update Chrome or load dist manually in a regular Chrome profile. Do not use a browser launched with --disable-extensions.",
      );
    }
    const existing = installed.find((extension) =>
      samePath(extension.path, build.folder),
    );
    let previous;
    try {
      previous = JSON.parse(
        await readFile(path.join(profile, "tompathy-review.json"), "utf8"),
      );
    } catch {}
    const unchanged =
      existing?.enabled &&
      previous?.extensionId === existing.id &&
      previous?.build === info.fingerprint;
    const id = unchanged
      ? existing.id
      : (await cdp.send("Extensions.loadUnpacked", { path: build.folder })).id;
    const verified = (
      await cdp.send("Extensions.getExtensions")
    ).extensions.find((extension) => extension.id === id);
    if (
      !verified?.enabled ||
      verified.version !== build.version ||
      !samePath(verified.path, build.folder)
    ) {
      throw Error(
        "Chrome did not confirm the expected extension as enabled. Inspect chrome://extensions in the review profile.",
      );
    }
    const reviewUrl = `chrome-extension://${id}/review.html`;
    const context = browser.contexts()[0];
    const readingOpen =
      unchanged &&
      context
        .pages()
        .some(
          (page) =>
            page.url().split("?")[0] === `chrome-extension://${id}/panel.html`,
        );
    const receipt = {
      verifiedAt: new Date().toISOString(),
      chromeVersion: browser.version(),
      extensionId: id,
      version: build.version,
      build: info.fingerprint,
      enabled: true,
      reusedBrowser,
      action: unchanged
        ? "Resumed existing installation"
        : existing
          ? "Updated installation"
          : previous
            ? "Restored installation"
            : "Installed extension",
      reviewUrl,
      readingLeftOpen: !!readingOpen,
    };
    await writeFile(
      path.join(profile, "tompathy-review.json"),
      JSON.stringify(receipt, null, 2),
    );
    if (showGuide && !readingOpen) {
      const guide =
        context.pages().find((page) => page.url() === reviewUrl) ??
        (await context.newPage());
      await guide.goto(reviewUrl);
      await guide.bringToFront();
    }
    return { browser, cdp, receipt, launchedProcess };
  } catch (error) {
    if (launchedProcess) {
      const cleanup = await browser.newBrowserCDPSession().catch(() => null);
      await cleanup?.send("Browser.close").catch(() => {});
    }
    await browser.close();
    throw error;
  }
}
