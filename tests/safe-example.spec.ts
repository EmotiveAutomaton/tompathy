import { test, expect } from "@playwright/test";
import { build } from "esbuild";

test("AI outer borders stay above cells and partial shared seams remain thin", async ({ page }) => {
  const compiled = await build({stdin: {resolveDir: process.cwd(), loader: "tsx", contents: `
    import React from 'react';
    import {createRoot} from 'react-dom/client';
    import {AIOutlines} from './src/components/AIOutlines';
    const tiles=[{key:'a',node:{id:'a'},path:'M20,20 H80 V100 H20 Z'},
      {key:'b',node:{id:'b'},path:'M80,20 H140 V60 H80 Z'},
      {key:'c',node:{id:'c'},path:'M80,60 H140 V100 H80 Z'}];
    const marks=new Map(['a','b'].map(id=>[id,{confidence:1,involvement:'ghost',description:'Constructed geometry fixture'}]));
    createRoot(document.getElementById('root')).render(<svg xmlns="http://www.w3.org/2000/svg" width="180" height="120" viewBox="0 0 180 120">
      <rect width="180" height="120" fill="white"/>
      {tiles.map(t=><path key={t.key} d={t.path} fill="#dbe8dd" stroke="#fbfcf8" strokeWidth="1.6"/>)}
      <AIOutlines tiles={tiles} marks={marks} width={180} height={120}/>
    </svg>);`}, bundle: true, format: "iife", write: false, define: {"process.env.NODE_ENV": '"production"'}});
  await page.setContent('<div id="root"></div>');
  await page.addScriptTag({content: compiled.outputFiles[0].text});
  await expect(page.locator(".ai-outline-outer")).toHaveCount(2);
  const pixels = await page.locator("svg").evaluate(async svg => {
    const url = URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(svg)], {type: "image/svg+xml"}));
    try {
      const img = new Image();
      await new Promise<void>((resolve, reject) => {img.onload=()=>resolve();img.onerror=reject;img.src=url;});
      const canvas = document.createElement("canvas"); canvas.width=720;canvas.height=480;
      const ctx=canvas.getContext("2d")!; ctx.drawImage(img,0,0,720,480);
      const red = (x:number,y:number) => {const p=ctx.getImageData(x,y,1,1).data;return Math.max(0,p[0]-p[1]);};
      // Non-scaling SVG strokes keep their physical width even in this larger
      // raster. Compare integrated red coverage, not a fourfold stroke width.
      const energy = (x:number,y:number) => Array.from({length:25},(_,i)=>red(x*4+i-12,y*4)).reduce((a,b)=>a+b,0);
      return {shared:energy(80,40),exposed:energy(80,80),outer:energy(20,40)};
    } finally {URL.revokeObjectURL(url);}
  });
  expect(pixels.shared).toBeGreaterThan(0);
  expect(pixels.exposed).toBeGreaterThan(pixels.shared * 3);
  expect(pixels.outer).toBeGreaterThan(pixels.shared * 3);
  expect(pixels.exposed).toBeGreaterThan(150);
  await page.screenshot({path:"evidence/ai-adjacent-borders.png"});
});

test("safe example uses current value artwork and explicit AI attribution", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", e => errors.push(e.message));
  await page.goto("/?demo=fieldnotes");
  const toggle = page.getByRole("checkbox", { name: "Mark likely AI" });
  await expect(toggle).toBeVisible();
  await expect(page.locator(".ai-marked")).toHaveCount(0);
  await toggle.check();
  await expect(page.locator(".ai-marked")).toHaveCount(3);
  await expect(page.locator('.ai-marked[data-node="sentence-6-3"]')).toHaveCount(1);
  await expect(page.locator('.ai-marked[data-node="paragraph-6"]')).toHaveCount(0);
  for (const [id, confidence, width] of [["sentence-8-1", .94, 1], ["sentence-6-2", .915, 1.5], ["sentence-6-3", .99, 2]] as const) {
    const outline = page.locator(`.ai-outline-outer[data-ai-node="${id}"]`);
    expect(await outline.evaluate(el => Number(getComputedStyle(el).strokeOpacity))).toBeCloseTo(confidence);
    await expect(outline).toHaveAttribute("data-outline-width", String(width));
  }
  await expect(page.locator(".pyramid svg > g > .ai-outline-layer:last-child")).toHaveCount(1);
  const control = await page.locator(".mark-ai").boundingBox();
  const heading = await page.locator(".process-region .section-heading h2").boundingBox();
  expect(control!.y).toBeGreaterThan(heading!.y + heading!.height);
  expect(Math.abs(control!.x + control!.width - heading!.x - heading!.width)).toBeLessThan(15);
  const box = await page.locator(".mark-ai-box").boundingBox();
  const cross = await page.locator(".mark-ai-box svg").boundingBox();
  expect(cross!.width).toBeGreaterThan(box!.width);
  expect(Math.abs(box!.x + box!.width / 2 - cross!.x - cross!.width / 2)).toBeLessThan(.6);
  expect(Math.abs(box!.y + box!.height / 2 - cross!.y - cross!.height / 2)).toBeLessThan(.6);
  await expect(page.locator(".values-region .support-wheel")).toHaveCount(0);
  await expect(page.locator(".values-region .value-category-icon").first()).toBeVisible();
  const seeking = page.getByRole("button", { name: "Drive SEEKING", exact: true });
  await expect(seeking).toBeVisible();
  await seeking.hover();
  await expect(page.locator(".hover-card .drive-brain")).toBeVisible();
  await page.mouse.move(20, 20);
  await toggle.evaluate(el => (el as HTMLElement).blur());
  await expect(page.locator(".mark-ai")).toHaveCSS("opacity", "1");
  await page.screenshot({ path: "evidence/safe-example-ai-mark.png" });
  await toggle.uncheck();
  await expect(page.locator(".ai-marked")).toHaveCount(0);
  expect(errors).toEqual([]);
});
