// Real CPU service lifecycle, cancellation and one post-cancellation decision.
import assert from "node:assert/strict";
import { readFile, writeFile } from "node:fs/promises";
import { startClef } from "./clef-session.mjs";

let service;
const report = { checkedAt: new Date().toISOString(), scientificAdmission: false };
try {
  service = await startClef();
  const { url, token } = service.connection;
  const headers = { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };
  const post = (body, extra = {}) => fetch(url + "/v1/systemone", {
    method: "POST", headers, body: JSON.stringify(body), signal: AbortSignal.timeout(130000), ...extra,
  });
  assert.equal((await fetch(url + "/v1/health")).status, 403);
  assert.equal((await fetch(url + "/v1/health", { headers: { ...headers, Origin: "https://example.org" } })).status, 403);
  assert.equal((await post({})).status, 400);
  assert.equal((await post({ state: "x".repeat(65000) })).status, 413);
  const fixture = JSON.parse(await readFile("scripts/fixtures/clef-smoke.json", "utf8"))[0];
  const controller = new AbortController();
  const pending = post(fixture.request, { signal: controller.signal }).catch(error => ({ error: error.name }));
  // Wait for real ownership of the worker, not a guessed delay before aborting.
  const deadline = Date.now() + 10000;
  let busy = false;
  while (Date.now() < deadline && !busy) {
    busy = (await post({})).status === 409;
    if (!busy) await new Promise(resolve => setTimeout(resolve, 100));
  }
  assert.ok(busy, "Real request did not acquire the worker");
  const cancelled = performance.now();
  controller.abort();
  await pending;
  let released = false;
  while (performance.now() - cancelled < 15000 && !released) {
    released = (await post({})).status === 400;
    if (!released) await new Promise(resolve => setTimeout(resolve, 100));
  }
  assert.ok(released, "Disconnected inference did not release its worker");
  report.cancelSeconds = (performance.now() - cancelled) / 1000;
  const response = await post(fixture.request);
  assert.equal(response.status, 200);
  report.response = await response.json();
  assert.equal(report.response.runtime.identity, service.connection.identity);
  assert.deepEqual(Object.keys(report.response.answers).sort(), Object.keys(fixture.request.questions).sort());
  report.health = service.health;
  report.passed = true;
} catch (error) {
  report.passed = false;
  report.error = error.message;
  throw error;
} finally {
  try { await service?.stop(); }
  catch (error) { report.passed = false; report.cleanupError = error.message; process.exitCode = 1; }
  if (service) {
    let alive = false;
    try { await fetch(service.connection.url + "/v1/health", { signal: AbortSignal.timeout(1000) }); alive = true; } catch {}
    report.ownedServiceClosed = !alive;
    if (alive) { report.passed = false; report.cleanupError = "Owned service remained reachable after shutdown"; process.exitCode = 1; }
  }
  await writeFile("evidence/clef-runtime-validation.json", JSON.stringify(report, null, 2));
  console.log(JSON.stringify({ passed: report.passed, cancelSeconds: report.cancelSeconds,
    seconds: report.response?.runtime.seconds, resources: report.response?.runtime,
    closed: report.ownedServiceClosed, error: report.error }));
}
