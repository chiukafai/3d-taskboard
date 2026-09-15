import { chromium } from './node_modules/playwright/index.mjs';
const BASE = 'http://127.0.0.1:8934/office-3d-taskboard.html';
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe' });
const page = await browser.newPage({ viewport: { width: 760, height: 760 }, deviceScaleFactor: 1.6 });
await page.goto(BASE, { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(10000);
await page.evaluate(() => {
  const d = window.__boardDebug;
  d.camera.fov = 22; d.camera.updateProjectionMatrix();
  d.camera.position.set(20, 9, 14.85);      // CFO 桌(20,14.4)+椅(20,13.9) 正上方
  d.controls.target.set(20, 0, 14.85);
  d.controls.update();
  ['toolbar','panel','legend','hint','syspanel'].forEach(id => { const e = document.getElementById(id); if (e) e.style.display = 'none'; });
});
await page.waitForTimeout(900);
await page.screenshot({ path: '../_shots/chair_top.png' });
console.log('saved chair_top.png');
await browser.close();
