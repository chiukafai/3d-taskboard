// 验证 file:// 双击打开场景是否可用（决定是否本地化依赖）
import { chromium } from './node_modules/playwright/index.mjs';
const FILE = 'file:///C:/Users/Perfect/Desktop/3d-taskboard-main/office-3d-taskboard.html';
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe' });
const page = await browser.newPage();
const errs = [];
page.on('console', m => { if (m.type() === 'error') errs.push(m.text().slice(0, 160)); });
page.on('pageerror', e => errs.push('PAGEERROR: ' + String(e).slice(0, 160)));
const t0 = Date.now();
await page.goto(FILE, { waitUntil: 'domcontentloaded' }).catch(e => console.log('goto 失败', e.message));
await page.waitForTimeout(12000);
const st = await page.evaluate(() => ({
  three: typeof window.__boardDebug !== 'undefined',
  models: !!window.OFFICE_MODELS,
  shows: window.__showCount || 0,
  doorGroups: window.__boardDebug ? Object.keys(window.__boardDebug.doorGroups).length : -1,
  canvas: !!document.querySelector('canvas'),
}));
console.log('=== file:// 直开测试 ===');
console.log('three 模块加载:', st.three, '| 模型包:', st.models, '| 已加载房数:', st.shows, '| 门:', st.doorGroups, '| canvas:', st.canvas);
console.log('耗时:', Date.now() - t0, 'ms');
console.log('错误(前8条):');
errs.slice(0, 8).forEach(e => console.log('  -', e));
await page.screenshot({ path: '../_shots/file_proto.png' });
await browser.close();
