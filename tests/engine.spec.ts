import { test, expect, chromium } from "@playwright/test";
import {
  cp,
  mkdir,
  mkdtemp,
  readFile,
  writeFile,
  readdir,
} from "node:fs/promises";
import { existsSync } from "node:fs";
import { spawn, type ChildProcess } from "node:child_process";
import path from "node:path";
import { SessionSchema, PacketSchema } from "../src/core/model";
import { readingFile } from "../src/core/reading-file";

test("built extension opts into an authenticated Python companion", async () => {
  test.setTimeout(60000);
  const python =
    process.env.TOMPATHY_PYTHON ??
    path.resolve(
      process.platform === "win32"
        ? "engine/.venv/Scripts/python.exe"
        : "engine/.venv/bin/python",
    );
  test.skip(
    !process.env.TOMPATHY_PYTHON && !existsSync(python),
    "Install engine[dev] for the Python companion integration test.",
  );
  await mkdir(".local", { recursive: true });
  await mkdir("evidence", { recursive: true });
  const root = await mkdtemp(path.resolve(".local/engine-browser-"));
  await cp("dist", path.join(root, "extension"), { recursive: true });
  const manifestPath = path.join(root, "extension/manifest.json");
  const manifest = JSON.parse(await readFile(manifestPath, "utf8"));
  manifest.host_permissions = ["http://127.0.0.1/*"];
  await writeFile(manifestPath, JSON.stringify(manifest));
  const extension = path.join(root, "extension");
  let server: ChildProcess | undefined;
  const context = await chromium.launchPersistentContext("", {
    channel: "chromium",
    headless: true,
    args: [
      `--disable-extensions-except=${extension}`,
      `--load-extension=${extension}`,
    ],
  });
  try {
    const worker =
      context.serviceWorkers()[0] ??
      (await context.waitForEvent("serviceworker"));
    const extensionId = new URL(worker.url()).host;
    const token = "d".repeat(64);
    const tokenFile = path.join(root, "fixture-token");
    await writeFile(tokenFile, token);
    server = spawn(
      python,
      [
        "-m",
        "tompathy_engine.cli",
        "serve",
        "--port",
        "18765",
        "--token-file",
        tokenFile,
        "--extension-origin",
        `chrome-extension://${extensionId}`,
      ],
      { windowsHide: true, stdio: ["ignore", "pipe", "pipe"] },
    );
    let serverLog = "";
    server.stderr?.on("data", (data) => {
      serverLog += String(data);
    });
    await expect
      .poll(
        async () => {
          if (server!.exitCode !== null) throw Error(serverLog);
          try {
            return (
              await fetch("http://127.0.0.1:18765/v1/health", {
                headers: { Authorization: `Bearer ${token}` },
              })
            ).status;
          } catch {
            return 0;
          }
        },
        { timeout: 15000 },
      )
      .toBe(200);
    const source = await context.newPage();
    await source.goto("http://127.0.0.1:5173/fixture.html");
    const captured = await worker.evaluate(async () => {
      const source = (await chrome.tabs.query({})).find((t) =>
        t.url?.endsWith("/fixture.html"),
      )!;
      await chrome.scripting.executeScript({
        target: { tabId: source.id! },
        files: ["content.js"],
      });
      return chrome.tabs.sendMessage(source.id!, { type: "TOMPATHY_CAPTURE" });
    });
    await worker.evaluate(async (artifact) => {
      await chrome.storage.session.set({
        reading: {
          sessionVersion: "1.0",
          artifact,
          packet: null,
          scope: "artifact",
          context: [],
        },
      });
    }, captured.artifact);
    const panel = await context.newPage();
    const errors: string[] = [];
    const requests: string[] = [];
    panel.on("pageerror", (error) => errors.push(error.message));
    panel.on("request", (request) => {
      if (request.url().includes(":18765/v1/analyze"))
        requests.push(request.method());
    });
    await panel.setViewportSize({ width: 420, height: 1000 });
    await panel.goto(`chrome-extension://${extensionId}/panel.html`);
    await source.bringToFront();
    await worker.evaluate(async () => {
      const tab = (await chrome.tabs.query({})).find((t) =>
        t.url?.endsWith("/fixture.html"),
      )!;
      await chrome.runtime.sendMessage({
        type: "TOMPATHY_INVOKED",
        tabId: tab.id,
      });
    });
    await expect(
      panel.getByRole("heading", { name: "Ready for an account" }),
    ).toBeVisible();
    expect(requests).toEqual([]);
    await panel
      .getByRole("button", { name: "Reader menu", exact: true })
      .click();
    await expect(
      panel.getByRole("combobox", { name: "Provider", exact: true }),
    ).toHaveValue("none");
    await panel
      .getByRole("combobox", { name: "Provider", exact: true })
      .selectOption("local");
    await panel
      .getByLabel("Source URL", { exact: true })
      .fill("http://127.0.0.1:18765");
    await panel.getByLabel("Companion token", { exact: true }).fill(token);
    await panel.getByRole("button", { name: "Save analysis source" }).click();
    await expect(
      panel.getByText("Saved. Choose Analyze capture to request a reading."),
    ).toBeVisible();
    await panel.screenshot({ path: "evidence/engine-provider-options.png" });
    expect(requests).toEqual([]);
    const expectedCapture = SessionSchema.parse(
      await worker.evaluate(
        async () => (await chrome.storage.session.get("reading")).reading,
      ),
    ).artifact;
    await panel
      .getByRole("button", { name: "Analyze capture", exact: true })
      .click();
    await expect(
      panel.getByText("Analysis received.", { exact: false }),
    ).toBeVisible();
    expect(requests).toEqual(["POST"]);
    const saved = SessionSchema.parse(
      await worker.evaluate(
        async () => (await chrome.storage.session.get("reading")).reading,
      ),
    );
    expect(saved.packet!.artifact).toEqual(expectedCapture);
    expect(saved.packet!.hypotheses).toEqual([]);
    expect(JSON.stringify(saved)).not.toContain(token);
    await panel.screenshot({ path: "evidence/engine-t0-reading.png" });
    expect(errors).toEqual([]);
    await writeFile(
      "evidence/engine-browser.json",
      JSON.stringify(
        {
          browser: context.browser()?.version(),
          build: JSON.parse(await readFile("dist/build-info.json", "utf8")),
          checks: [
            "default none sends no analysis",
            "explicit local configuration",
            "authenticated real Python analysis",
            "exact artifact returned",
            "T0 contains no invented hypotheses",
            "token excluded from reading",
            "zero panel errors",
          ],
          surface:
            "Built extension document and webpage adapter; native toolbar placement checked separately",
        },
        null,
        2,
      ),
    );
  } finally {
    await context.close();
    if (server && server.exitCode === null) {
      // This exact child was launched above; never stop an unrelated companion.
      server.kill();
      await new Promise<void>((resolve) => {
        server!.once("exit", () => resolve());
        setTimeout(resolve, 5000);
      });
    }
  }
});

test("engine readings render recorded history and population comparisons", async () => {
  test.setTimeout(120000);
  const extension = path.resolve("dist");
  const context = await chromium.launchPersistentContext("", {
    channel: "chromium",
    headless: true,
    args: [
      `--disable-extensions-except=${extension}`,
      `--load-extension=${extension}`,
    ],
  });
  try {
    const worker =
      context.serviceWorkers()[0] ??
      (await context.waitForEvent("serviceworker"));
    const id = new URL(worker.url()).host;
    const panel = await context.newPage();
    const errors: string[] = [];
    panel.on("pageerror", (e) => errors.push(e.message));
    await panel.setViewportSize({ width: 420, height: 1000 });
    await panel.goto(`chrome-extension://${id}/panel.html`);
    const directory =
      process.env.TOMPATHY_READING_DIR ?? "engine/tests/fixtures/packets";
    const files = (await readdir(directory)).filter(
      (f) => f.endsWith(".json") && f !== "selected-context.json",
    );
    const receipt = [];
    for (const file of files) {
      const packet = PacketSchema.parse(
        JSON.parse(await readFile(path.join(directory, file), "utf8")),
      );
      const session = SessionSchema.parse({
        sessionVersion: "1.0",
        artifact: packet.artifact,
        packet,
        scope: "artifact",
        context: [],
      });
      await panel
        .getByRole("button", { name: "Reader menu", exact: true })
        .click();
      await panel.getByLabel("Import reading", { exact: true }).setInputFiles({
        name: "reading.html",
        mimeType: "text/html",
        buffer: Buffer.from(readingFile(session)),
      });
      await expect(
        panel.getByRole("button", { name: "Reader menu", exact: true }),
      ).toBeVisible();
      await expect
        .poll(
          async () =>
            SessionSchema.parse(
              await worker.evaluate(
                async () =>
                  (await chrome.storage.session.get("reading")).reading,
              ),
            ).packet?.id,
        )
        .toBe(packet.id);
      if (packet.process.nodes.length) {
        await expect(
          panel.getByLabel("Recorded production history"),
        ).toBeVisible();
        await expect(
          panel.locator(".recorded-process li").first(),
        ).toBeVisible();
      }
      await panel.screenshot({
        path: `evidence/engine-${path.basename(file, ".json")}.png`,
      });
      if (packet.population) {
        await panel.getByRole("tab", { name: "global", exact: true }).click();
        await expect(panel.getByLabel("Population comparison")).toContainText(
          packet.population.populationId,
        );
        const firstMaker = packet.makers[0].id;
        const comparisons = packet.population.items.filter((i) =>
          packet.hypotheses
            .find((h) => h.id === i.hypothesis)
            ?.makers.includes(firstMaker),
        );
        if (comparisons.length)
          await expect(
            panel
              .getByRole("img", {
                name: "Supplied uncertainty width by number of records",
              })
              .first(),
          ).toBeVisible();
        await panel.screenshot({
          path: `evidence/engine-${path.basename(file, ".json")}-population.png`,
        });
        await panel
          .getByRole("tab", { name: "current work only", exact: true })
          .click();
      }
      receipt.push({
        file,
        regions: packet.artifact.regions.length,
        processEvents: packet.process.nodes.length,
        populationItems: packet.population?.items.length ?? 0,
      });
    }
    expect(errors).toEqual([]);
    await writeFile(
      "evidence/engine-readings-render.json",
      JSON.stringify(
        {
          browser: context.browser()?.version(),
          surface: "Built extension document; imported exact reading snapshots",
          readings: receipt,
          errors,
        },
        null,
        2,
      ),
    );
  } finally {
    await context.close();
  }
});
