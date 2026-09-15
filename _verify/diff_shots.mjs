// 视觉回归：优化前(_fps_before) vs 优化后，同机位截图
import { chromium } from './node_modules/playwright/index.mjs';
const shots = [
  ['overview', ''],
  ['ceo', '?zone=ceo'],
  ['cmo', '?zone=cmo'],
  ['cfo', '?zone=cfo'],
];
const targets = [
  ['before', 'http://127.0.0.1:8934/_fps_before.html'],
  ['after',  'http://127.0.0.1:8934/office-3d-taskboard.html'],
];
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe' });
for (const [tag, url] of targets) {
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  for (const [name, qs] of shots) {
    await page.goto(url + qs, { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => window.__showCount >= 8, null, { timeout: 60000 }).catch(() => {});
    await page.waitForTimeout(2500);
    await page.screenshot({ path: `../_shots/diff_${tag}_${name}.png` });
    console.log('shot', tag, name);
  }
  await page.close();
}
await browser.close();
