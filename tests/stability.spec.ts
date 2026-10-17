import { test, expect, type Page } from "@playwright/test";
import { readFile, writeFile } from "node:fs/promises";
import { createExample } from "../src/core/example";
import { PacketSchema, type Packet } from "../src/core/model";
import type { GoalNode } from "../src/core/hierarchy";
import { readingFile, parseReadingFile } from "../src/core/reading-file";

async function show(page: Page, packet: Packet) {
  await page.goto("/?panel&demo=fieldnotes");
  await page.evaluate((packet) => {
    localStorage.setItem("tompathy-guide-offered-040", "yes");
    sessionStorage.setItem(
      "tompathy-session",
      JSON.stringify({
        sessionVersion: "1.0",
        artifact: packet.artifact,
        packet,
        scope: "artifact",
        context: [],
      }),
    );
  }, packet);
  await page.reload();
}

test("teardrop handles solitary, deep, wide, shared and dense structures without losing navigation", async ({
  page,
}) => {
  test.setTimeout(60000);
  await page.setViewportSize({ width: 360, height: 800 });
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const base = await createExample("https://example.org/graph-stress-fixture");
  const node = (i: number): GoalNode => ({
    id: `stress-${i}`,
    maker: base.makers[0].id,
    label:
      i === 0
        ? "A very long supplied label — 日本語 العربية 🌞 — that still needs a reachable home"
        : "Goal " + i,
    description: "Constructed stress structure",
    regions: base.artifact.regions.map((r) => r.id),
    evidence: [],
  });
  const cases: [string, GoalNode[]][] = [
    ["solitary", [node(0)]],
    [
      "deep",
      Array.from({ length: 64 }, (_, i) => ({
        ...node(i),
        ...(i < 63 ? { parentIds: [`stress-${i + 1}`] } : {}),
      })),
    ],
    [
      "wide",
      [
        ...Array.from({ length: 160 }, (_, i) => ({
          ...node(i),
          parentIds: ["stress-160"],
        })),
        node(160),
      ],
    ],
    [
      "shared",
      [
        { ...node(0), parentIds: ["stress-1", "stress-2"] },
        { ...node(1), parentIds: ["stress-3"] },
        node(2),
        node(3),
      ],
    ],
    ["dense", Array.from({ length: 1901 }, (_, i) => node(i))],
  ];
  for (const [name, nodes] of cases) {
    const packet = structuredClone(base);
    packet.goalHierarchy = { nodes };
    packet.hypotheses.forEach((h) => delete h.decisionNodes);
    PacketSchema.parse(packet);
    await show(page, packet);
    await expect(page.locator("[data-node]")).toHaveCount(nodes.length);
    const geometry = await page
      .locator('[data-testid="process"] svg')
      .evaluateAll((els) => els.map((e) => e.outerHTML).join(""));
    expect(geometry).not.toMatch(/NaN|Infinity/);
    if (name === "dense") {
      await expect(page.locator(".pyramid-list")).toBeVisible();
      await page.locator('[data-node="stress-0"]').focus();
      await page.keyboard.press("ArrowDown");
      await expect(page.locator('[data-node="stress-1"]')).toBeFocused();
    } else {
      await page.locator('[data-node="stress-0"]').focus();
      await page.keyboard.press("Enter");
      await expect(page.locator(".process-lock")).toBeVisible();
    }
    if (name === "shared")
      await page.screenshot({ path: "evidence/stability-shared-graph.png" });
    await page.keyboard.press("Escape");
  }
  expect(errors).toEqual([]);
});

test("trajectory points expose supplied values and sleeves through keyboard and pointer", async ({
  page,
}) => {
  await page.setViewportSize({ width: 360, height: 800 });
  await show(page, await createExample());
  await page
    .getByRole("button", { name: "Care for others", exact: true })
    .click();
  const dialog = page.getByRole("dialog");
  const slider = dialog.getByRole("slider", {
    name: "Inspect supplied trajectory points",
  });
  await slider.focus();
  await page.keyboard.press("Home");
  await expect(slider).toHaveAttribute("aria-valuenow", "1");
  await expect(dialog.locator(".preference-readout")).toContainText("Point 1");
  await page.keyboard.press("ArrowRight");
  await expect(slider).toHaveAttribute("aria-valuenow", "2");
  const box = (await slider.boundingBox())!;
  await page.mouse.move(box.x + box.width - 2, box.y + box.height / 2);
  const last = await slider.getAttribute("aria-valuemax");
  await expect(slider).toHaveAttribute("aria-valuenow", last!);
  await expect(dialog.locator(".preference-inspection")).toBeVisible();
  await expect(
    dialog.locator(".preference-observations li").first(),
  ).toContainText("supplied cost");
  await page.screenshot({ path: "evidence/stability-trajectory.png" });
});

test("real engine fit exports structured intervals that render at narrow width", async ({
  page,
}) => {
  // Includes a cold dev-server load, file import, screenshot and a second reading.
  test.setTimeout(60000);
  const packet = PacketSchema.parse(
    JSON.parse(
      await readFile(
        "engine/tests/fixtures/packets/constructed-preferences.json",
        "utf8",
      ),
    ),
  );
  expect(packet.schemaVersion).toBe("1.8");
  const value = packet.hypotheses.find((h) => h.preferenceEstimate)!;
  expect(value).toBeTruthy();
  const portable = readingFile({
    sessionVersion: "1.0",
    artifact: packet.artifact,
    packet,
    scope: "artifact",
    context: [],
  });
  expect((await parseReadingFile(portable)).packet?.schemaVersion).toBe("1.8");
  await writeFile("evidence/engine-interval-reading.html", portable);
  await page.setViewportSize({ width: 360, height: 800 });
  await page.goto("/?panel&demo=fieldnotes");
  await page.getByRole("button", { name: "Reader menu", exact: true }).click();
  await page
    .getByLabel("Import reading", { exact: true })
    .setInputFiles("evidence/engine-interval-reading.html");
  await page.getByRole("tab", { name: "creator", exact: true }).click();
  await page.getByRole("button", { name: value.label, exact: true }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog.locator(".preference-estimate")).toBeVisible();
  await expect(dialog.locator(".preference-chart")).toHaveAccessibleName(
    /95% interval/,
  );
  await expect(dialog.locator(".preference-sleeve")).toHaveCount(1);
  await dialog.getByText("Observed evidence", { exact: true }).click();
  await expect(dialog.locator("blockquote").first()).toContainText("Observed");
  await dialog.getByText("Observed evidence", { exact: true }).click();
  expect(
    await dialog
      .locator("svg")
      .evaluateAll((els) => els.map((e) => e.outerHTML).join("")),
  ).not.toMatch(/NaN|Infinity/);
  const bounds = (await dialog.boundingBox())!;
  expect(bounds.x).toBeGreaterThanOrEqual(0);
  expect(bounds.x + bounds.width).toBeLessThanOrEqual(360);
  await page.screenshot({ path: "evidence/stability-engine-interval.png" });
  await page.keyboard.press("Escape");
  value.preferenceEstimate!.interval = null;
  await show(page, packet);
  await page.getByRole("tab", { name: "creator", exact: true }).click();
  await page.getByRole("button", { name: value.label, exact: true }).click();
  await expect(
    page.getByRole("dialog").locator(".preference-sleeve"),
  ).toHaveCount(0);
  await expect(page.getByRole("dialog")).toContainText(
    "Uncertainty not supplied",
  );
});
