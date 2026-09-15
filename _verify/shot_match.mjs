// 按用户截图同尺寸渲染全景，便于逐像素对比定位
import { chromium } from './node_modules/playwright/index.mjs';

const URL = 'http://127.0.0.1:8934/office-3d-taskboard.html';
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe' });
const page = await browser.newPage({ viewport: { width: 956, height: 461 }, deviceScaleFactor: 2 });
await page.goto(URL, { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(12000);
const st = await page.evaluate(() => ({ show: window.__showCount, cam: window.__boardDebug ? 'ok' : 'no' }));
console.log('showCount=', st.show, 'debug=', st.cam);
await page.screenshot({ path: '../_shots/m_overview.png' });
console.log('saved m_overview.png');
await browser.close();
