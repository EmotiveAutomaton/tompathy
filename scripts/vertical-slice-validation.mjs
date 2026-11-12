// One real blog, one disposable native panel, real local CPU readers.
import { expect } from '@playwright/test';
import { mkdtemp, writeFile, rm, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { startPractice } from './practice-session.mjs';
import { openReview } from './chrome-review.mjs';

const local = path.resolve('.local');
const profile = await mkdtemp(path.join(local, 'vertical-slice-'));
const receipt = { checkedAt:new Date().toISOString(), url:'https://sive.rs/relax', errors:[], consoleErrors:[], samples:[], phases:[], startupLog:[] };
const connections=[];
let session, panel;
try {
  receipt.judgmentsEnabled = process.env.TOMPATHY_TEST_SURFACE_ONLY !== '1';
  const previewCache=process.env.TOMPATHY_TEST_COLD === '1' ? await mkdtemp(path.join(local,'vertical-slice-cache-')) : undefined;
  receipt.cacheMode=previewCache ? 'fresh isolated scoring cache' : 'shared exact-call cache';
  const startup=performance.now();
  session = await startPractice({profile, previewCache, judgments:receipt.judgmentsEnabled, log:line => { receipt.startupLog.push(line); console.log(line); }});
  receipt.startupSeconds=(performance.now()-startup)/1000;
  connections.push(session.review.browser);
  Object.assign(receipt,{browser:session.review.receipt.chromeVersion,build:session.review.receipt.build,implementation:session.implementation});
  const context=session.review.browser.contexts()[0], id=session.review.receipt.extensionId;
  const source=await context.newPage();
  await source.goto(`chrome-extension://${id}/review.html`);
  await source.getByRole('link',{name:/Open the safe example/}).click();
  await source.getByRole('button',{name:'Open Maker Reader'}).click();
  const attached=await openReview({profile,showGuide:false});connections.push(attached.browser);
  panel=attached.browser.contexts()[0].pages().find(p=>p.url().includes('/panel.html'));
  if(!panel)throw Error('Native side panel absent');
  panel.on('pageerror',e=>receipt.errors.push(e.message));
  panel.on('console',e=>{if(e.type()==='error')receipt.consoleErrors.push(e.text());});
  const landscape=panel.locator('.values-landscape');
  await expect(landscape.getByRole('table',{name:'Core values hierarchy'})).toBeVisible();
  const care=landscape.getByRole('button',{name:'Drive CARE',exact:true});
  await care.focus();
  await panel.screenshot({path:'evidence/values-native-table.png'});
  await care.press('Enter');
  await expect(panel.locator('.modal .preference-vector')).toHaveCount(3);
  await panel.keyboard.press('Escape');
  receipt.valuesNative=true;
  const settings=await context.newPage(); await settings.goto('chrome://extensions/');
  await settings.evaluate(async id=>{for(const origin of ['http://*/*','https://*/*']) await chrome.developerPrivate.addHostPermission(id,origin);},id);
  await settings.close();
  const guide=session.page;await guide.bringToFront();
  await guide.getByRole('button',{name:/Connect local engine/}).click();
  await expect(guide.locator('#connection')).toContainText('Connected to engine');
  await guide.getByRole('button',{name:/Enable Follow pages/}).click();
  await expect(guide.locator('#following')).toContainText('Follow pages is on');
  receipt.permissionSetup='Chrome settings API in disposable profile; actual Follow pages UI. Native first-use consent is manual.';
  const started=Date.now();
  await source.bringToFront();await source.goto(receipt.url,{waitUntil:'domcontentloaded',timeout:45000});
  const read=()=>panel.evaluate(async()=>(await chrome.storage.session.get('reading')).reading);
  await expect.poll(async()=>(await read())?.artifact?.source,{timeout:20000}).toBe(receipt.url);
  const capture=(await read()).artifact;
  receipt.captureSeconds=(Date.now()-started)/1000;
  receipt.capture={title:capture.title,revision:capture.revision,regions:capture.regions.length,words:capture.regions.reduce((n,r)=>n+r.anchor.exact.split(/\s+/).length,0)};
  await writeFile('.local/vertical-slice-capture.json',JSON.stringify(capture));
  receipt.commentsCaptured=capture.regions.some(r=>r.anchor.exact.includes('RoJean')||r.anchor.exact.includes('The simplicity of this is just beautiful'));
  receipt.contextMetadata=await source.evaluate(()=>({authorLinks:document.querySelectorAll('a[rel~="author"], [itemprop="author"] a[itemprop="url"]').length, jsonLd:document.querySelectorAll('script[type="application/ld+json"]').length}));
  await panel.getByRole('button',{name:'Reader menu',exact:true}).click();
  await panel.getByRole('checkbox',{name:/^Light context/}).check();
  receipt.lightContextEnabled=true;
  await panel.keyboard.press('Escape');
  console.log(JSON.stringify({capture:receipt.capture,commentsCaptured:receipt.commentsCaptured}));
  await expect(panel.locator('.reader-content.is-ready.research-preview')).toBeVisible({timeout:45000});
  receipt.firstReadingSeconds=(Date.now()-started)/1000;
  await panel.screenshot({path:'evidence/blog-first-reading.png'});
  // Observe this UI request to completion, including progressive module counts.
  const deadline=Date.now()+220000;
  let final;
  while(Date.now()<deadline){
    const current=await read();
    const statuses=await panel.locator('.reading-progress-item').evaluateAll(es=>es.map(e=>e.getAttribute('aria-label')));
    const elapsed=(Date.now()-started)/1000;
    if(JSON.stringify(receipt.samples.at(-1)?.statuses)!==JSON.stringify(statuses))receipt.samples.push({seconds:elapsed,statuses});
    if(current?.packet?.artifact.source===receipt.url){final=current;break;}
    await new Promise(r=>setTimeout(r,2000));
  }
  if(!final)throw Error('Automatic live request did not finish in its bounded test window');
  receipt.finalSeconds=(Date.now()-started)/1000;
  receipt.modules=final.packet.preview.modules;
  receipt.cachedAt=final.packet.preview.cachedAt;
  receipt.hypotheses=final.packet.hypotheses.length;
  receipt.hierarchyNodes=final.packet.goalHierarchy?.nodes.length??0;
  receipt.context=final.context.map(c=>({kind:c.kind,status:c.status,title:c.title,source:c.source}));
  receipt.admissions=final.packet.provider.admissions;
  receipt.resumable=final.packet.preview.resumable;
  await writeFile('.local/vertical-slice-packet.json',JSON.stringify(final.packet));
  console.log(JSON.stringify({seconds:receipt.finalSeconds,modules:receipt.modules}));
  expect(final.packet.provider.id).toBe('tompathy-engine');
  expect(final.packet.provider.admissions).toEqual([]);
  expect(final.packet.artifact).toEqual(final.artifact);
  expect(receipt.commentsCaptured).toBe(false);
  receipt.continuations=[];
  for(let pass=0; pass<2 && final.packet.preview.resumable; pass++) {
    const began=performance.now();
    await panel.getByRole('button',{name:'Continue reading',exact:true}).click();
    await expect(panel.getByRole('button',{name:'Cancel analysis',exact:true})).toBeVisible();
    await expect(panel.getByRole('button',{name:'Cancel analysis',exact:true})).toBeHidden({timeout:200000});
    final=await read();
    receipt.continuations.push({seconds:(performance.now()-began)/1000,modules:final.packet.preview.modules});
  }
  receipt.finalModules=final.packet.preview.modules;
  receipt.availableModulesComplete=receipt.finalModules.every(m=>['complete','unavailable'].includes(m.status));
  receipt.context=final.context.map(c=>({source:c.source,author:c.provenance?.author,basis:c.provenance?.basis,selected:c.selected}));
  expect(receipt.context.some(c=>c.author==='Derek Sivers'&&c.basis==='page-byline'&&c.selected===false)).toBe(true);
  await writeFile('.local/vertical-slice-packet.json',JSON.stringify(final.packet));
  const marks=source.locator('[data-tompathy-mark]');
  receipt.markedPassages=await marks.count();
  await expect(marks).toHaveCount(capture.regions.length);
  await marks.first().hover({position:{x:12,y:12}});
  await marks.first().click({position:{x:12,y:12}});
  await expect(panel.locator('.reader-content > .sr-only[role="status"]')).toContainText('Locked');
  receipt.sentenceLock=true;
  await source.keyboard.press('Escape');
  await panel.mouse.move(0,0);
  await panel.screenshot({path:'evidence/blog-native-result.png'});
  await source.screenshot({path:'evidence/blog-native-source.png'});
  await panel.getByRole('tab',{name:'global',exact:true}).click();
  await expect(panel.getByRole('region',{name:'Public population research'})).toContainText('Sounding Line EV3');
  receipt.researchReturnVisible=true;
  await panel.getByRole('tab',{name:'current work only',exact:true}).click();
  // Warm replay through the same companion; preserve normal live settings.
  const setup=await guide.evaluate(async()=>(await chrome.storage.session.get('tompathy-practice-setup'))['tompathy-practice-setup']);
  const warm=performance.now();
  const response=await fetch(setup.url+'/v1/analyze',{method:'POST',headers:{Authorization:`Bearer ${setup.token}`,'Content-Type':'application/json'},signal:AbortSignal.timeout(20000),
    body:JSON.stringify({requestId:crypto.randomUUID(),artifact:capture,scope:'artifact',mode:'preview',preferCache:true})});
  if(!response.ok)throw Error(`Warm replay HTTP ${response.status}`);
  const replay=await response.json();
  receipt.warmReplaySeconds=(performance.now()-warm)/1000;receipt.warmCachedAt=replay.preview.cachedAt;
  expect(replay.artifact.revision).toBe(capture.revision);
  expect(receipt.errors).toEqual([]);
  receipt.passed=true;
} catch(error){receipt.passed=false;receipt.failure=error.stack;throw error;}
finally {
  try{await session?.stop();receipt.servicesStopped=true;}catch(error){receipt.cleanupError=error.message;}
  await session?.review.cdp.send('Browser.close').catch(()=>{});
  for(const browser of connections)await browser.close().catch(()=>{});
  if(path.dirname(profile)!==local||!path.basename(profile).startsWith('vertical-slice-'))throw Error('Unexpected cleanup path');
  try{await rm(profile,{recursive:true,force:true,maxRetries:6,retryDelay:500});receipt.profileRemoved=true;}catch(error){receipt.profileCleanupError=error.message;}
  await mkdir('evidence',{recursive:true});await writeFile('evidence/vertical-slice-blog.json',JSON.stringify(receipt,null,2));
  console.log(JSON.stringify(receipt,null,2));
}
