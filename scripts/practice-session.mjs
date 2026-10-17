import { access, mkdir, readFile, writeFile } from "node:fs/promises";
import { spawn, execFile } from "node:child_process";
import { promisify } from "node:util";
import { createHash, randomBytes } from "node:crypto";
import { createServer } from "node:net";
import path from "node:path";
import { openReview } from "./chrome-review.mjs";
import { startFixedQwen } from "./fixed-qwen-session.mjs";
import { startClef } from "./clef-session.mjs";

const pause = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
export async function startPractice({
  profile = path.resolve(".local/chrome-review"),
  log = console.log,
  judgments = true,
  clef = process.env.TOMPATHY_CLEF === "1",
  preparationBudget = 165,
  previewCache = path.resolve(".local/preview-score-cache"),
} = {}) {
  const root = path.resolve(".");
  const admissions = path.join(root, ".local/engine-question-admissions");
  let questionAdmissions = null;
  try {
    const complete = await readFile(path.join(admissions, "complete.receipt"), "utf8");
    const receipt = JSON.parse(complete);
    const names = ["Q1.json", "Q3.json", "Q4.json", "Q5.json", "Q7.json", "Q8.json", "Q9.json"];
    if (JSON.stringify(Object.keys(receipt.files).sort()) !== JSON.stringify(names))
      throw Error("Incomplete question receipt set");
    for (const name of names) {
      const actual = createHash("sha256").update(await readFile(path.join(admissions, name))).digest("hex");
      if (actual !== receipt.files[name]) throw Error("Question receipt hash mismatch");
    }
    questionAdmissions = createHash("sha256").update(complete).digest("hex");
  } catch (error) {
    if (error.code !== "ENOENT") throw Error(`Cannot load question receipts: ${error.message}`);
  }
  if (!judgments) questionAdmissions = null;
  if (!Number.isInteger(preparationBudget) || preparationBudget < 165 || preparationBudget > 600)
    throw Error("Preparation budget must be 165–600 seconds");
  const python =
    process.env.TOMPATHY_PYTHON ??
    path.join(
      root,
      process.platform === "win32"
        ? "engine/.venv/Scripts/python.exe"
        : "engine/.venv/bin/python",
    );
  try {
    await access(python);
  } catch {
    throw Error(
      "Install the local engine first: create engine/.venv, then install -e engine using that environment’s Python. See docs/LIVE_PRACTICE.md.",
    );
  }
  const env = {
    ...process.env,
    OPENBLAS_NUM_THREADS: "1",
    OMP_NUM_THREADS: "1",
  };
  const { stdout } = await promisify(execFile)(
    python,
    [
      "-c",
      "from tompathy_engine.admission import implementation_hash; print(implementation_hash())",
    ],
    { cwd: root, windowsHide: true, env },
  );
  const implementation = stdout.trim();
  if (!/^[0-9a-f]{64}$/.test(implementation))
    throw Error("Could not identify the local engine.");
  const review = await openReview({ profile, showGuide: false });
  const folder = path.join(path.resolve(profile), "tompathy-engine");
  await mkdir(folder, { recursive: true });
  const tokenFile = path.join(folder, "token");
  let server,
    setup,
    savedConnection,
    logTail = "",
    launchError, fixedQwen, clefService;
  const stop = async () => {
    const errors = [];
    // Windows venv launchers can have a real Python child. Close only the
    // exact tree created here, and still attempt both model cleanups on error.
    try {
      if (server && server.exitCode === null && !server.killed) {
        const ended = new Promise((resolve) => server.once("exit", resolve));
        if (process.platform === "win32")
          await promisify(execFile)("taskkill", ["/PID", String(server.pid), "/T", "/F"], { windowsHide: true });
        else server.kill();
        await Promise.race([ended, pause(5000)]);
      }
    } catch (error) { errors.push(error); }
    for (const service of [fixedQwen, clefService]) {
      try { await service?.stop(); } catch (error) { errors.push(error); }
    }
    if (errors.length) throw new AggregateError(errors, "Owned practice process cleanup failed");
  };
  try {
    let previous;
    try {
      const record = JSON.parse(
        await readFile(path.join(folder, "connection.json"), "utf8"),
      );
      const token = (await readFile(tokenFile, "utf8")).trim();
      if (
        /^http:\/\/127\.0\.0\.1:\d+$/.test(record.url) &&
        /^[0-9a-f]{64}$/.test(token)
      ) {
        savedConnection = { url: record.url, token };
        const response = await fetch(`${record.url}/v1/health`, {
          headers: { Authorization: `Bearer ${token}` },
          signal: AbortSignal.timeout(1200),
          redirect: "error",
        });
        if (response.ok)
          previous = { ...record, token, health: await response.json() };
      }
    } catch {
      /* A stopped companion is started below; no unrelated port is reclaimed. */
    }
    if (previous) {
      if (
        previous.implementation !== implementation ||
        previous.health.implementationHash !== implementation ||
        Boolean(previous.clef) !== clef ||
        (previous.questionAdmissions ?? null) !== questionAdmissions ||
        (previous.preparationBudget ?? 165) !== preparationBudget ||
        previous.extensionId !== review.receipt.extensionId
      )
        throw Error(
          "This review Chrome session is using an older engine. Close the ToMpathy review Chrome windows, then run Practice ToMpathy again. Your regular Chrome windows can stay open.",
        );
      setup = { url: previous.url, token: previous.token, implementation };
    } else {
      // Show a useful starting state while the owned model is loading.
      const context = review.browser.contexts()[0];
      const guideUrl = `chrome-extension://${review.receipt.extensionId}/practice.html`;
      const loadingPage = context.pages().find(p => p.url() === guideUrl) ?? await context.newPage();
      await loadingPage.goto(guideUrl);
      await loadingPage.evaluate(async () => {
        await chrome.storage.session.remove("tompathy-practice-setup");
        document.getElementById("connect").disabled = true;
        document.getElementById("connection").textContent = "Starting the local engine. This may take a minute…";
      });
      await loadingPage.bringToFront();
      if (clef) clefService = await startClef({ log });
      if (judgments) fixedQwen = await startFixedQwen({ log });
      const socket = createServer();
      await new Promise((resolve, reject) => {
        socket.once("error", reject);
        socket.listen(0, "127.0.0.1", resolve);
      });
      const port = socket.address().port;
      await new Promise((resolve) => socket.close(resolve));
      const token = randomBytes(32).toString("hex");
      await writeFile(tokenFile, token, { mode: 0o600 });
      setup = { url: `http://127.0.0.1:${port}`, token, implementation };
      server = spawn(
        python,
        [
          "-m",
          "tompathy_engine.cli",
          "serve",
          "--port",
          String(port),
          "--token-file",
          tokenFile,
          "--extension-origin",
          `chrome-extension://${review.receipt.extensionId}`,
          "--history-dir",
          path.join(folder, "history"),
          "--preview-readers",
          path.join(root, ".local/preview-readers"),
          "--preview-cache",
          previewCache,
          "--preview-preparation-budget", String(preparationBudget),
          ...(fixedQwen ? ["--preview-judgment-url", fixedQwen.url] : []),
          ...(fixedQwen && questionAdmissions ? ["--preview-question-admissions", admissions] : []),
          ...(clefService ? ["--preview-clef-config", clefService.config] : []),
        ],
        {
          cwd: root,
          env,
          windowsHide: true,
          stdio: ["ignore", "ignore", "pipe"],
        },
      );
      server.on("error", (error) => {
        launchError = error;
      });
      server.stderr.on("data", (data) => {
        logTail = (logTail + String(data)).slice(-12000);
        log(String(data).trimEnd());
      });
      let healthy = false;
      const deadline = Date.now() + 60000;
      while (!healthy && Date.now() < deadline) {
        if (launchError || server.exitCode !== null)
          throw Error(
            `The companion did not start. ${launchError?.message ?? logTail}`,
          );
        try {
          const response = await fetch(`${setup.url}/v1/health`, {
            headers: { Authorization: `Bearer ${token}` },
            signal: AbortSignal.timeout(800),
            redirect: "error",
          });
          healthy =
            response.ok &&
            (await response.json()).implementationHash === implementation;
        } catch {
          /* Bounded startup wait. */
        }
        if (!healthy) await pause(150);
      }
      if (!healthy)
        throw Error("The companion did not become ready within 60 seconds.");
      await writeFile(
        path.join(folder, "connection.json"),
        JSON.stringify(
          {
            url: setup.url,
            implementation,
            extensionId: review.receipt.extensionId,
            clef,
            questionAdmissions,
            preparationBudget,
          },
          null,
          2,
        ),
      );
    }
    const context = review.browser.contexts()[0];
    const url = `chrome-extension://${review.receipt.extensionId}/practice.html`;
    const page =
      context.pages().find((p) => p.url() === url) ?? (await context.newPage());
    await page.goto(url);
    // Restore only a previously selected practice connection. First use or a
    // different provider still requires the explicit Connect gesture.
    await page.evaluate(
      async ({ setup, savedConnection }) => {
        await chrome.storage.session.set({ "tompathy-practice-setup": setup });
        const provider = (await chrome.storage.local.get("tompathy-provider"))[
          "tompathy-provider"
        ];
        if (
          provider?.kind === "local" &&
          savedConnection &&
          provider.url === savedConnection.url &&
          provider.token === savedConnection.token
        )
          await chrome.storage.local.set({
            "tompathy-provider": {
              kind: "local",
              url: setup.url,
              token: setup.token,
            },
          });
      },
      { setup, savedConnection },
    );
    await page.bringToFront();
    return {
      review,
      page,
      stop,
      server,
      reused: !!previous,
      folder,
      implementation,
      url: setup.url,
    };
  } catch (error) {
    try { await stop(); }
    finally {
      if (review.launchedProcess)
        await review.cdp.send("Browser.close").catch(() => {});
      await review.browser.close();
    }
    throw error;
  }
}
