// 逐房近景：看门 + 门牌 + 家具的真实相对位置
import { chromium } from './node_modules/playwright/index.mjs';

const BASE = 'http://127.0.0.1:8934/office-3d-taskboard.html';
const rooms = process.argv.slice(2);
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe' });
for (const r of rooms) {
  const page = await browser.newPage({ viewport: { width: 1000, height: 720 }, deviceScaleFactor: 1.5 });
  await page.goto(BASE + '?zone=' + r, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(9000);
  await page.screenshot({ path: `../_shots/z_${r}.png` });
  console.log('saved z_' + r + '.png');
  await page.close();
}
await browser.close();
