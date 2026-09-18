/** 修复后取证：总览 + CMO|CTO 共墙接缝特写。用法：node _verify/shots_zfight.mjs */
import { chromium } from './node_modules/playwright/index.mjs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const target = 'http://127.0.0.1:8934/office-3d-taskboard.html';
const out = n => path.resolve(here, '../_shots/' + n);

const browser = await chromium.launch({
  headless: true,
  executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
});
const page = await browser.newPage({ viewport: { width: 1200, height: 760 }, deviceScaleFactor: 1.4 });
const errs = []; page.on('pageerror', e => errs.push(String(e)));
await page.goto(target, { waitUntil: 'load' });
await page.waitForFunction(() => window.__boardDebug && window.__boardDebug.scene, { timeout: 90000 });
await page.waitForTimeout(6000);                       // 等开场动画走完
await page.screenshot({ path: out('zfight_overview.png') });

const views = [
  ['zfight_seam_cmo_cto', [26.0, 1.60, 6.6], [23.8, 1.45, 6.6]],   // 站 CTO 内看 x=23.8 共墙
  ['zfight_seam_coo_ceo', [21.5, 1.60, 15.6], [19.4, 1.45, 15.6]], // 站 CEO 内看 x=19.4 共墙
];
for (const [name, pos, look] of views) {
  await page.evaluate(([p, l]) => {
    const d = window.__boardDebug;
    d.controls.enabled = false; d.controls.enableDamping = false;
    d.camera.position.set(p[0], p[1], p[2]);
    d.controls.target.set(l[0], l[1], l[2]);
    d.camera.lookAt(l[0], l[1], l[2]);
  }, [pos, look]);
  await page.waitForTimeout(900);
  await page.screenshot({ path: out(name + '.png') });
}
console.log('页面报错:', errs.length ? errs : '无');
await browser.close();
