import { chromium } from './node_modules/playwright/index.mjs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const target = 'file:///' + path.resolve(here, '../平面图方案-错落曲线版.html').replace(/\\/g, '/');

const browser = await chromium.launch({
  headless: true,
  executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
});
const page = await browser.newPage({ viewport: { width: 1180, height: 1180 }, deviceScaleFactor: 1.5 });
const errs = [];
page.on('pageerror', e => errs.push(String(e)));
await page.goto(target, { waitUntil: 'load' });
await page.waitForTimeout(800);
await page.screenshot({ path: path.resolve(here, '../_shots/plan_v3_light.png'), fullPage: true });
await page.evaluate(() => document.body.classList.add('dark'));
await page.waitForTimeout(400);
await page.screenshot({ path: path.resolve(here, '../_shots/plan_v3_dark.png'), fullPage: true });
console.log('errors:', errs.length ? errs : 'none');
await browser.close();
