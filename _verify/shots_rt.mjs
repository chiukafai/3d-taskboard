// 用离屏 RT 取图（可靠版）：门牌朝向 / CFO 地毯 / 桌面
import { chromium } from './node_modules/playwright/index.mjs';
import { rtShot, look } from './grab.mjs';
const BASE = 'http://127.0.0.1:8934/office-3d-taskboard.html';
const OUT = 'C:/Users/Perfect/Desktop/3d-taskboard-main/_shots/';
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe' });
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
await page.goto(BASE, { waitUntil: 'domcontentloaded' });
await page.waitForFunction(() => !!window.__boardDebug, { timeout: 20000 });
await page.waitForTimeout(16000);

const VIEWS = [
  ['r0_overview', [14.8, 20.6, 30.4], [14.8, 0, 10.8]],
  ['r1_cfo_plaque', [11.4, 2.10, 18.0], [8.74, 2.35, 17.5]],
  ['r2_cpo_plaque', [9.4, 2.10, 7.4], [6.74, 2.35, 7.4]],
  ['r3_cfo_rugs', [5.4, 7.0, 20.6], [5.4, 0.0, 18.6]],
  ['r4_cro_desk', [12.9, 1.85, 6.30], [12.5, 0.80, 4.45]],
  ['r5_ceo_desk', [22.9, 1.85, 16.60], [21.8, 0.80, 14.60]],
  ['r6_cmo_desks', [20.4, 2.20, 3.20], [19.6, 0.80, 2.05]],
];
for (const [n, cam, tgt] of VIEWS) { await look(page, ...cam, ...tgt); await rtShot(page, OUT + n + '.png'); console.log('  ✓', n); }
await browser.close();
console.log('done');
