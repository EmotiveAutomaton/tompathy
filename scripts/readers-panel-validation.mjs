import { expect } from '@playwright/test';
import { mkdtemp, mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { openReview } from './chrome-review.mjs';

await mkdir('evidence', { recursive: true });
const profile = await mkdtemp(path.resolve('.local/readers-panel-'));
let current;
const connections = [];
const receipt = { at: new Date().toISOString(), checks: [], errors: [] };
try {
  current = await openReview({ profile }); connections.push(current.browser);
  receipt.browser = current.receipt.chromeVersion; receipt.build = current.receipt.build;
  const context = current.browser.contexts()[0];
  const source = await context.newPage();
  await source.goto(new URL('example.html', current.receipt.reviewUrl).href);
  const widthBefore = await source.evaluate(() => innerWidth);
  await source.getByRole('button', { name: 'Open Maker Reader' }).click();
  current = await openReview({ profile, showGuide: false }); connections.push(current.browser);
  const panel = current.browser.contexts()[0].pages().find(p => p.url().includes('/panel.html'));
  if (!panel) throw Error('Native panel did not open');
  panel.on('pageerror', e => receipt.errors.push(e.message));
  await expect(panel.getByTestId('needs-landscape')).toBeVisible();
  await expect(panel.locator('.need-target')).toHaveCount(7);
  await expect(panel.locator('.body-subchannel')).toHaveCount(3);
  await expect(panel.locator('.need-caption,.need-meta,.need-column-label')).toHaveCount(0);
  await expect.poll(() => source.evaluate(() => innerWidth)).toBeLessThan(widthBefore);
  const dismissal = panel.getByRole('button', { name: 'Dismiss interaction guide' });
  if (await dismissal.count()) await dismissal.click();
  await panel.getByTestId('needs-landscape').screenshot({ path: 'evidence/readers-v2-rest.png' });
  await panel.locator('.need-source').first().hover();
  await expect(panel.locator('.need-source.connected')).not.toHaveCount(0);
  const vectorOpacity = await panel.locator('.need-connections').evaluate(svg => ({
    lit: Array.from(svg.querySelectorAll('g.lit')).map(g => +getComputedStyle(g).opacity),
    quiet: Array.from(svg.querySelectorAll('g:not(.lit)')).map(g => +getComputedStyle(g).opacity),
    endpoints: Array.from(svg.querySelectorAll('g')).map(g => [g.getAttribute('data-to'), g.querySelector('.need-vector').getAttribute('d')]),
  }));
  await expect.poll(async () => panel.locator('.need-connections g.lit').first().evaluate(g => +getComputedStyle(g).opacity)).toBeGreaterThan(.8);
  expect(vectorOpacity.quiet.every(o => o < .08)).toBe(true);
  expect(new Set(vectorOpacity.endpoints.map(p => p.join(':'))).size).toBe(vectorOpacity.endpoints.length);
  receipt.vectorEndpoints = vectorOpacity.endpoints.length;
  await panel.getByTestId('needs-landscape').screenshot({ path: 'evidence/readers-v2-fluency-hover.png' });
  await panel.locator('.need-target').first().click();
  await expect(panel.getByRole('heading', { name: 'Competence', exact: true })).toBeVisible();
  await expect(panel.locator('.need-details')).toContainText('notional illustration');
  await panel.screenshot({ path: 'evidence/readers-v2-need-detail.png' });
  await panel.keyboard.press('Escape');
  await expect(panel.locator('.need-details')).toHaveCount(0);
  await panel.locator('.need-target').first().focus();
  await panel.keyboard.press('Enter');
  await expect(panel.locator('.need-details')).toBeVisible();
  await panel.keyboard.press('Escape');
  await panel.locator('.need-target').first().hover();
  await expect(panel.locator('.need-connections .lit')).not.toHaveCount(0);
  await expect(panel.locator('.need-related')).not.toHaveCount(0);
  await panel.screenshot({ path: 'evidence/readers-v2-current-artifact.png', fullPage: true });
  for (const name of ['Heat', 'Food', 'Sleep', 'Stress']) {
    await panel.getByTestId('needs-landscape').getByRole('button', { name, exact: true }).click();
    await expect(panel.getByRole('heading', { name, exact: true })).toBeVisible();
    await panel.keyboard.press('Escape');
  }
  await expect(panel.locator('.need-pigtail')).toHaveCount(1);
  receipt.checks.push('Native Chrome panel; five needs, Body, Heat/Food/Sleep and Stress; distinct faint vectors; hover and cross-panel links; mouse/keyboard detail views; Escape');
  await panel.getByRole('tab', { name: 'author', exact: true }).click();
  await expect(panel.locator('.need-source.action[data-current="true"]')).toBeVisible();
  const overflows = await panel.locator('.need-scene').evaluate(e => e.scrollWidth > e.clientWidth + 1);
  expect(overflows).toBe(false);
  await panel.screenshot({ path: 'evidence/readers-v2-author.png', fullPage: true });
  receipt.checks.push('Author action uses full teardrop, current artifact visible, no horizontal overflow');
  expect(receipt.errors).toEqual([]);
} finally {
  if (current) await current.cdp.send('Browser.close').catch(() => {});
  for (const b of connections) await b.close().catch(() => {});
  await writeFile('evidence/readers-v2-panel-validation.json', JSON.stringify(receipt, null, 2));
}
console.log(JSON.stringify(receipt));
