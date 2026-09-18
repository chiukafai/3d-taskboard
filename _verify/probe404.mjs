/* 定位页面加载后的 4xx/5xx 请求与 JS 错误 —— 用于确认"控制台是否干净"。
   用法：node probe404.mjs [url]  （默认 8934 静态预览） */
import { chromium } from './node_modules/playwright/index.mjs';

const URL = process.argv[2] || 'http://127.0.0.1:8934/office-3d-taskboard.html';
const b = await chromium.launch({
  headless: true,
  executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
});
const p = await b.newPage();
const bad = [];      // 真·问题：4xx/5xx、控制台报错、页面异常、请求失败
const api = [];      // 信息性：发起了哪些 api/favicon 请求（不是错误，别混进 bad 里）
p.on('response', r => { if (r.status() >= 400) bad.push(r.status() + '  ' + r.url()); });
p.on('console', m => {
  if (m.type() === 'error') {
    const loc = m.location();
    bad.push('CONSOLE  ' + m.text() + '   @' + (loc.url || '?') + ':' + (loc.lineNumber ?? '?'));
  }
});
p.on('pageerror', e => bad.push('PAGEERR  ' + e.message));
p.on('requestfailed', r => bad.push('FAILED  ' + r.url() + '  ' + (r.failure() || {}).errorText));
p.on('request', r => { if (/\/api\/|favicon/.test(r.url())) api.push(r.url()); });
await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
await p.waitForTimeout(9000);
console.log('URL =', URL);
console.log('--- 4xx/5xx 与错误 ---');
console.log(bad.length ? bad.join('\n') : '（无）');
/* 期望值：静态预览（8934）应为 0 —— 说明"没连服务就一个请求都不发"；
   服务托管（8787）应为 1 —— 只发 /api/tasks.json，且不应有 /api/health 之类的探测。 */
console.log('--- 发起的 api 请求（信息性，非错误）---');
console.log(api.length ? api.join('\n') : '（0 个 —— 没配数据源时完全不发请求）');
await b.close();
