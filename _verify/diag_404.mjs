// 列出看板加载失败的具体资源（用于定位 404）
import { chromium } from 'playwright';
const URL = 'http://127.0.0.1:8934/office-3d-taskboard.html';
const browser = await chromium.launch({
  headless: true,
  executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
  args: ['--no-sandbox', '--disable-dev-shm-usage']
});
const page = await (await browser.newContext()).newPage();
const bad = [];
page.on('response', r => { if (r.status() >= 400) bad.push(r.status() + '  ' + r.url()); });
page.on('requestfailed', r => bad.push('FAIL  ' + r.url() + '  (' + (r.failure()?.errorText || '') + ')'));
await page.goto(URL, { waitUntil: 'load', timeout: 30000 });
await page.waitForTimeout(8000);
const data = await page.evaluate(() => ({
  taskData: typeof window.TASK_DATA,
  taskDataKeys: window.TASK_DATA ? Object.keys(window.TASK_DATA).length : 0,
  taskInbox: typeof window.TASK_INBOX,
  hasModels: !!window.__boardDebug
}));
await browser.close();
console.log('=== 加载失败资源 ===');
bad.length ? bad.forEach(b => console.log('  ' + b)) : console.log('  无');
console.log('\n=== 数据管线状态 ===');
console.log('  window.TASK_DATA  :', data.taskData, data.taskData ? `(${data.taskDataKeys} 个部门)` : '');
console.log('  window.TASK_INBOX :', data.taskInbox);
console.log('  3D 场景就绪        :', data.hasModels ? '✅' : '❌');
