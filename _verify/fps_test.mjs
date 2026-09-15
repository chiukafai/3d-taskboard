// FPS 测量：静置 4 秒统计平均帧率（参数=URL）
import { chromium } from './node_modules/playwright/index.mjs';
const URL = process.argv[2];
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe' });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
await page.goto(URL, { waitUntil: 'domcontentloaded' });
await page.waitForFunction(() => window.__showCount >= 8, null, { timeout: 60000 }).catch(() => {});
await page.waitForTimeout(1500);
const fps = await page.evaluate(() => new Promise(res => {
  let n = 0; const t0 = performance.now();
  function tick() { n++; if (performance.now() - t0 < 4000) requestAnimationFrame(tick); else res(n / ((performance.now() - t0) / 1000)); }
  requestAnimationFrame(tick);
}));
console.log(URL.split('/').pop(), '→ 平均帧率', fps.toFixed(1), 'FPS');
await browser.close();
