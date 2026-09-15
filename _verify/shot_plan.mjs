// 正俯视平面图：看清每间房门洞位置 + 门牌位置
import { chromium } from './node_modules/playwright/index.mjs';

const BASE = 'http://127.0.0.1:8934/office-3d-taskboard.html';
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe' });
const page = await browser.newPage({ viewport: { width: 1100, height: 850 }, deviceScaleFactor: 1.4 });
await page.goto(BASE, { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(11000);
await page.evaluate(() => {
  const d = window.__boardDebug;
  d.camera.fov = 30; d.camera.updateProjectionMatrix();
  d.camera.position.set(12, 46, 9.001);
  d.controls.target.set(12, 0, 9);
  d.controls.update();
  // 隐藏 UI 遮挡
  ['toolbar','panel','legend','hint','syspanel'].forEach(id => { const e = document.getElementById(id); if (e) e.style.display = 'none'; });
});
await page.waitForTimeout(1200);
await page.screenshot({ path: '../_shots/plan_top.png' });
console.log('saved plan_top.png');
await browser.close();
