import { test, expect } from "./built-page";
import { readFile } from "node:fs/promises";

test("preview preserves timeline locations, unread density and closed field badges", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", e => errors.push(e.message));
  const packet = JSON.parse(await readFile("engine/tests/fixtures/packets/week-preview.json", "utf8"));
  // A saved status cannot bypass the current snapshot's missing reader gate.
  packet.hypotheses.find((h: {finding?: string}) => h.finding === "departure-phrase").evidenceStatus = "field-tested";
  await page.addInitScript(packet => sessionStorage.setItem("tompathy-session", JSON.stringify({ sessionVersion: "1.0", artifact: packet.artifact, packet, scope: "artifact", context: [] })), packet);
  await page.goto("/");
  await expect(page.locator(".reader-content.is-ready")).toBeVisible();
  await expect(page.locator(".evidence-field-tested")).toHaveCount(0);
  await page.locator(".attention-timeline summary").click();
  await expect(page.locator(".attention-timeline")).toContainText("Not located in surviving text");
  await page.locator(".attention-timeline button.text-button").first().click();
  await page.getByRole("checkbox", { name: "Departure density · untested" }).check();
  const unread = page.locator('.pyramid [data-node="group-p3"] title');
  await expect(unread).toContainText("not read");
  await expect(page.locator('.pyramid [data-node="group-p1"] title')).toContainText("may track rare words and topic changes");
  await expect(page.getByRole("table", { name: "Core values hierarchy" })).toBeVisible();
  await page.screenshot({ path: "evidence/week-preview.png" });
  expect(errors).toEqual([]);
});
