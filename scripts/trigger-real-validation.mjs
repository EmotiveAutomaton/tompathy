// Native-panel acceptance using an exact saved research packet, no new inference.
import { expect } from '@playwright/test';
import { readFile, writeFile, mkdtemp } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import path from 'node:path';
import { openReview } from './chrome-review.mjs';

const job = path.resolve(process.argv[2] ?? '.local/trigger/ts3-worry-a');
if (!job.startsWith(path.resolve('.local') + path.sep)) throw Error('Private acceptance job required');
const verification = JSON.parse(await readFile(path.join(job, 'exit-verification.json'), 'utf8'));
const result = JSON.parse(await readFile(path.join(job, 'receipt.json'), 'utf8'));
if (result.card !== 'TS3-real' || result.status !== 'complete' ||
    !['nativeExited', 'releaseMatches', 'sharedLeaseAbsent', 'localLeaseAbsent'].every(k => verification[k]))
  throw Error('Verify completed acceptance job and exact release first');
const bytes = await readFile(path.join(job, 'packets/essay-1.json'));
const packet = JSON.parse(bytes.toString('utf8'));
if (!packet.bottom_box.on_page.some(r => r.id === 'S1' && r.series.length)) throw Error('Saved essay has no real worry series');
const decision = JSON.parse(await readFile('src/core/worry-lift-decision.json', 'utf8'));
const scalar = packet.bottom_box.on_page.find(r => r.id === 'S1');
const lift = decision.pack === scalar.pack && Boolean(decision.sourceReceiptPin);
const target = lift ? await mkdtemp(path.resolve('.local/word-table/ui-tp33-'))
  : await mkdtemp(path.resolve('.local/trigger/ui-' + path.basename(job) + '-'));
const profile = await mkdtemp(path.resolve('.local/trigger-real-chrome-'));
const escape = s => s.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');
const receipt = { at: new Date().toISOString(), scope: 'Exact saved real research packet in native panel, private public-corpus replay',
  packetPin: createHash('sha256').update(bytes).digest('hex'), checks: [], errors: [] };
let current;
const connections = [];
try {
  current = await openReview({ profile }); connections.push(current.browser);
  const context = current.browser.contexts()[0];
  // Fulfil only this synthetic capture URL locally; no external essay request.
  await context.route(packet.artifact.source, route => route.fulfill({ contentType: 'text/html', body:
    `<!doctype html><meta charset="utf-8"><title>${escape(packet.artifact.title)}</title><main style="max-width:44rem;margin:3rem auto;font:20px/1.7 Georgia">${packet.artifact.regions.map(r => `<p>${escape(r.anchor.exact)}</p>`).join('')}</main>` }));
  const settings = await context.newPage();
  await settings.goto('chrome://extensions/');
  await settings.evaluate(async ({ id, origin }) => chrome.developerPrivate.addHostPermission(id, origin + '/*'),
    { id: current.receipt.extensionId, origin: new URL(packet.artifact.source).origin });
  await settings.close();
  const source = await context.newPage();
  await source.goto(packet.artifact.source);
  const before = await source.evaluate(() => innerWidth);
  const targets = await current.cdp.send('Target.getTargets', { filter: [{ type: 'tab' }] });
  const sourceTarget = targets.targetInfos.find(t => t.url === source.url());
  await current.cdp.send('Extensions.triggerAction', { id: current.receipt.extensionId, targetId: sourceTarget.targetId });
  current = await openReview({ profile, showGuide: false }); connections.push(current.browser);
  const panel = current.browser.contexts()[0].pages().find(p => p.url().includes('/panel.html'));
  if (!panel) throw Error('Native panel not found');
  panel.on('pageerror', e => receipt.errors.push(e.message));
  await expect.poll(() => source.evaluate(() => innerWidth)).toBeLessThan(before);
  await expect.poll(() => panel.evaluate(async () => Boolean((await chrome.storage.session.get('reading')).reading?.artifact))).toBe(true);
  await panel.evaluate(async packet => {
    const { reading } = await chrome.storage.session.get('reading');
    reading.artifact = packet.artifact; reading.packet = packet;
    await chrome.storage.session.set({ reading });
    localStorage.setItem('tompathy-research-preview', 'true');
  }, packet);
  await panel.reload();
  const dismiss = panel.getByRole('button', { name: 'Dismiss interaction guide' });
  if (await dismiss.count()) await dismiss.click();
  await panel.getByTestId('needs-landscape').getByRole('button', { name: 'Stress', exact: true }).click();
  const worry = panel.getByTestId('research-stress');
  if (lift) {
    const filed = JSON.parse(await readFile('engine/validation/readers-worry-lift-2026-11.json', 'utf8'));
    expect(filed.sourceReceiptPin).toEqual(decision.sourceReceiptPin);
    expect(filed.researchDisplayPasses).toEqual(true);
    expect(filed.essays[0].shown).toEqual(0);
    await expect(worry).toHaveCount(0);
    await panel.screenshot({ path: path.join(target, 'essay-stress.png') });
    receipt.checks.push('Verified native research view on the exact saved essay with zero qualifying windows.');
    // Change only the disposable browser fixture. Never modify source packets or research forecasts.
    const fixture = structuredClone(packet);
    const windows = fixture.bottom_box.on_page.find(r => r.id === 'S1').series;
    windows.forEach((s, i) => { s.value = i === 0 ? .625 : .5; });
    await panel.evaluate(async fixture => {
      const { reading } = await chrome.storage.session.get('reading');
      reading.packet = fixture;
      await chrome.storage.session.set({ reading });
    }, fixture);
    await panel.reload();
    await panel.getByTestId('needs-landscape').getByRole('button', { name: 'Stress', exact: true }).click();
    await expect(worry.getByRole('listitem')).toHaveCount(1);
    await expect(worry.getByRole('listitem')).toHaveText(`Characters ${windows[0].from}–${windows[0].to} · +1.00 points`);
    await worry.screenshot({ path: path.join(target, 'constructed-boundary.png') });
    receipt.checks.push('Constructed threshold case rendered only the one window exactly 1.00 point above its page median.');
    receipt.decision = decision;
  } else {
    await expect(worry).toContainText('5.95 of 9');
    await expect(worry).toContainText('not a measure of this writer');
    await expect(worry.locator('circle')).toHaveCount(scalar.series.length);
    await panel.screenshot({ path: path.join(target, 'essay-stress.png') });
    receipt.checks.push('Native side panel beside the original essay replay rendered the saved level series.');
  }
  await panel.keyboard.press('Escape');
  await panel.evaluate(() => localStorage.setItem('tompathy-research-preview', 'false'));
  await panel.reload();
  await panel.getByTestId('needs-landscape').getByRole('button', { name: 'Stress', exact: true }).click();
  await expect(panel.getByTestId('research-stress')).toHaveCount(0);
  receipt.checks.push('Research off hides real worry series; maker tier remains empty');
  expect(packet.bottom_box.about_maker).toEqual([]); expect(receipt.errors).toEqual([]);
  receipt.browser = current.receipt.chromeVersion; receipt.build = current.receipt.build;
} finally {
  if (current) await current.cdp.send('Browser.close').catch(() => {});
  for (const browser of connections) await browser.close().catch(() => {});
  await writeFile(path.join(target, 'verification.json'), JSON.stringify(receipt, null, 2));
}
console.log(JSON.stringify(receipt));
