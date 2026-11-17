import { expect } from '@playwright/test';
import { mkdtemp, mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { openReview } from './chrome-review.mjs';

await mkdir('evidence', { recursive: true });
const profile = await mkdtemp(path.resolve('.local/trigger-panel-'));
let current;
const connections = [];
const receipt = { at: new Date().toISOString(), scope: 'Constructed TS3 software fixture, no empirical reading', checks: [], errors: [] };
try {
  current = await openReview({ profile }); connections.push(current.browser);
  receipt.browser = current.receipt.chromeVersion; receipt.build = current.receipt.build;
  const context = current.browser.contexts()[0];
  const source = await context.newPage();
  await source.goto(new URL('example.html', current.receipt.reviewUrl).href);
  const before = await source.evaluate(() => innerWidth);
  await source.getByRole('button', { name: 'Open Maker Reader' }).click();
  current = await openReview({ profile, showGuide: false }); connections.push(current.browser);
  const panel = current.browser.contexts()[0].pages().find(p => p.url().includes('/panel.html'));
  if (!panel) throw Error('Native panel did not open');
  panel.on('pageerror', e => receipt.errors.push(e.message));
  await expect(panel.getByTestId('needs-landscape')).toBeVisible();
  await expect.poll(() => source.evaluate(() => innerWidth)).toBeLessThan(before);
  await panel.evaluate(async () => {
    const { reading } = await chrome.storage.session.get('reading');
    if (!reading?.packet) throw Error('Missing example session');
    const region = reading.packet.artifact.regions[0];
    const start = region.anchor.start, end = start + region.anchor.exact.length;
    reading.packet.schemaVersion = '1.11';
    const common = { tier: 'on_page', share: null, events: [], series: [], pack: `constructed@${'a'.repeat(64)}`,
      key: { corpus: 'constructed', labelled_by: 'software test author', n: 3 },
      score: { metric: 'constructed control', value: 1, interval: null }, people: {}, floor: {}, nothing_here: {},
      mapping: { status: 'proposed', source: 'Constructed interface test' }, status: 'research' };
    reading.packet.bottom_box = { version: 'bottom-box-2', about_maker: [], toolbox: [], on_page: [{
      id: 'S1', tier: 'on_page', share: null, events: [], pack: `constructed@${'a'.repeat(64)}`,
      key: { corpus: 'constructed', labelled_by: 'software test author', n: 3 },
      score: { metric: 'constructed control', value: 1, interval: null }, people: {}, floor: {},
      nothing_here: { theme_free_mean_normalized: .5 }, mapping: { status: 'proposed', source: 'Constructed interface test' },
      status: 'research', series: [{ from: start, to: end, value: .2 }],
    }, { ...common, id: null, events: [{ span: [start, end], label: 'romance', confidence: .7, who: 'unclear', words: [] }] },
    { ...common, id: 'C3', events: [{ span: [start, end], label: 'fear', confidence: .8, who: 'unclear', words: [],
      stake: { need: 'N2', direction: 'threatened', by: 'self', when: 'ahead', mapping: common.mapping },
      channel_by_table: { channel: 'C2', version: 'trigger-table-1' } }] }] };
    await chrome.storage.session.set({ reading });
    localStorage.setItem('tompathy-research-preview', 'true');
  });
  await panel.reload();
  const dismiss = panel.getByRole('button', { name: 'Dismiss interaction guide' });
  if (await dismiss.count()) await dismiss.click();
  await panel.getByTestId('needs-landscape').getByRole('button', { name: 'Stress', exact: true }).click();
  await expect(panel.getByTestId('research-stress')).toBeVisible();
  await expect(panel.getByTestId('research-stress')).toContainText('Constructed software fixture');
  await expect(panel.getByTestId('research-stress')).toContainText('5.00 of 9');
  await expect(panel.locator('.need-details')).not.toContainText('notional illustration');
  await panel.screenshot({ path: 'evidence/trigger-constructed-stress.png' });
  receipt.checks.push('Native side panel beside unchanged source; constructed research scalar renders its series and plain-prose caption');
  await panel.keyboard.press('Escape');
  await panel.getByRole('button', { name: 'Reader menu', exact: true }).click();
  await panel.getByTestId('research-readings').locator('summary').first().click();
  await panel.getByText('Unassigned labels · 1 events', { exact: true }).click();
  await expect(panel.getByTestId('research-readings')).toContainText('romance · score 0.700 · no assigned need or channel');
  await panel.getByText('FEAR · 1 events', { exact: true }).click();
  await expect(panel.getByTestId('research-readings')).toContainText('RAGE (disagrees with the label reader)');
  await panel.screenshot({ path: 'evidence/trigger-constructed-events.png' });
  receipt.checks.push('Unassigned tag and table/label disagreement are inspectable beside their actual passage');
  await panel.keyboard.press('Escape');
  await panel.evaluate(() => localStorage.setItem('tompathy-research-preview', 'false'));
  await panel.reload();
  await panel.getByTestId('needs-landscape').getByRole('button', { name: 'Stress', exact: true }).click();
  await expect(panel.getByTestId('research-stress')).toHaveCount(0);
  await expect(panel.locator('.need-details')).toContainText('notional illustration');
  receipt.checks.push('Research off hides the measured-series path and retains the notional detail; Escape and click passed');
  expect(receipt.errors).toEqual([]);
} finally {
  if (current) await current.cdp.send('Browser.close').catch(() => {});
  for (const browser of connections) await browser.close().catch(() => {});
  await writeFile('evidence/trigger-panel-validation.json', JSON.stringify(receipt, null, 2));
}
console.log(JSON.stringify(receipt));
