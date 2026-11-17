// Native-panel acceptance using an exact saved research packet, no new inference.
import { expect } from '@playwright/test';
import { readFile, writeFile, mkdir, mkdtemp } from 'node:fs/promises';
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
const target = path.resolve('.local/trigger/ui-' + path.basename(job));
await mkdir(target, { recursive: true });
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
  await expect(panel.getByTestId('research-stress')).toContainText('5.95 of 9');
  await expect(panel.getByTestId('research-stress')).toContainText('not a measure of this writer');
  await expect(panel.getByTestId('research-stress').locator('circle')).toHaveCount(packet.bottom_box.on_page.find(r => r.id === 'S1').series.length);
  await panel.screenshot({ path: path.join(target, 'essay-stress.png') });
  receipt.checks.push('Native side panel beside exact public essay replay; every saved worry window rendered with its benchmark and plain-prose limit');
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
