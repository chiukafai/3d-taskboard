import { chromium } from './node_modules/playwright/index.mjs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const target = 'file:///' + path.resolve(here, '../平面图方案-非对称版.html').replace(/\\/g, '/');

const browser = await chromium.launch({
  headless: true,
  executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
});
const page = await browser.newPage({ viewport: { width: 1200, height: 1200 }, deviceScaleFactor: 1.5 });
const errs = [];
page.on('pageerror', e => errs.push(String(e)));
await page.goto(target, { waitUntil: 'load' });
await page.waitForTimeout(700);
await page.screenshot({ path: path.resolve(here, '../_shots/plan_v4_dark.png'), fullPage: true });
await page.evaluate(() => { document.body.dataset.theme = 'light'; });
await page.waitForTimeout(400);
await page.screenshot({ path: path.resolve(here, '../_shots/plan_v4_light.png'), fullPage: true });
const box = await page.evaluate(() => {
  const s = document.querySelector('svg').getBoundingClientRect();
  return { w: Math.round(s.width), h: Math.round(s.height) };
});
console.log('svg size:', JSON.stringify(box), 'errors:', errs.length ? errs : 'none');
await browser.close();
