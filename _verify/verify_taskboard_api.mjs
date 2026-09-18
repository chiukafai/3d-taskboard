// 端到端验证：taskboard 接入服务 + 看板实时同步 + 状态回写
// 用法: node verify_taskboard_api.mjs [base]   默认 http://127.0.0.1:8787
import { chromium } from 'playwright';

const BASE = (process.argv[2] || 'http://127.0.0.1:8787').replace(/\/+$/, '');
const ok = (b) => (b ? '✅' : '❌');
let fails = 0;
const chk = (label, pass, extra = '') => {
  if (!pass) fails++;
  console.log(`  ${ok(pass)} ${label}${extra ? '  — ' + extra : ''}`);
};

console.log('===== taskboard 端到端验证 =====');
console.log('BASE =', BASE, '\n');

// ---------- ① HTTP 接口 ----------
console.log('【1】HTTP 接口');
const health = await (await fetch(BASE + '/api/health')).json();
chk('GET /api/health', health.ok === true, `现有 ${health.tasks} 条任务`);

// 用「写在最后一行」的通用方式录任务：任何 agent 只要会发 HTTP 就行
const stamp = new Date().toISOString().slice(11, 19);
const post = await fetch(BASE + '/api/tasks', {
  method: 'POST', headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify([
    { title: `接口验证-中文别名 ${stamp}`, 部门: '财务', 状态: '进行中', 优先级: '高', source: 'verify-api' },
    { name: `接口验证-布尔旗标 ${stamp}`, zone: 'tech', urgent: true, done: false, source: 'verify-api' },
    { title: `接口验证-不写部门 ${stamp}`, source: 'verify-api' },
  ]),
});
const postJson = await post.json();
chk('POST /api/tasks 批量录入', post.ok && postJson.added === 3,
  `added=${postJson.added} updated=${postJson.updated} rejected=${postJson.rejected.length}`);

const single = await (await fetch(BASE + '/api/tasks', {
  method: 'POST', headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ title: `接口验证-单条 ${stamp}`, dept: 'meeting', source: 'verify-api' }),
})).json();
chk('POST /api/tasks 单条录入', single.added === 1, `total=${single.total}`);

const list = await (await fetch(BASE + '/api/tasks?source=verify-api')).json();
chk('GET  /api/tasks?source= 过滤', list.count >= 4, `命中 ${list.count} 条`);

const payload = await (await fetch(BASE + '/api/tasks.json')).json();
chk('GET  /api/tasks.json（看板数据）', !!payload.data, `total=${payload.stats.total}`);

const js = await (await fetch(BASE + '/api/tasks.js')).text();
chk('GET  /api/tasks.js（JS 直出）', js.includes('window.TASK_DATA'), `${js.length} 字节`);

const denied = await fetch(BASE + '/data/taskboard.db');
chk('内部文件不外泄（/data/… → 403）', denied.status === 403, `HTTP ${denied.status}`);
const denied2 = await fetch(BASE + '/taskboard/server.py');
chk('引擎源码不外泄（/taskboard/… → 403）', denied2.status === 403, `HTTP ${denied2.status}`);
// 隐私面：任务清单、截图、备份、配置都不能因为"托管看板"而暴露到局域网
for (const [p, label] of [
  ['/inbox/', '任务清单 inbox/'],
  ['/_shots/', '截图 _shots/'],
  ['/board.config.json', '配置文件'],
  ['/office-3d-taskboard.html.bak_pre_zfight_20260916', '备份 *.bak'],
  ['/WB看板配置-001.md', '文档 *.md'],
  ['/Dockerfile', 'Dockerfile'],
]) {
  const r = await fetch(BASE + p);
  chk(`隐私路径不外泄（${label} → 403）`, r.status === 403, `HTTP ${r.status}`);
}
const boardHtml = await fetch(BASE + '/office-3d-taskboard.html');
chk('看板静态托管', boardHtml.status === 200, `HTTP ${boardHtml.status}`);
const models = await fetch(BASE + '/all-models.js');
chk('模型包可访问（看板依赖）', models.status === 200, `HTTP ${models.status}`);
const emitted = await fetch(BASE + '/tasks-data/tasks.js');
chk('看板数据文件可访问（看板依赖）', emitted.status === 200, `HTTP ${emitted.status}`);

// ---------- ② 看板实时同步 ----------
console.log('\n【2】看板实时同步');
const browser = await chromium.launch({
  headless: true,
  executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
  args: ['--no-sandbox', '--disable-dev-shm-usage'],
});
const page = await (await browser.newContext({ viewport: { width: 1500, height: 940 } })).newPage();
const errs = [];
page.on('pageerror', (e) => errs.push('pageerror: ' + e.message));
await page.goto(BASE + '/office-3d-taskboard.html', { waitUntil: 'load', timeout: 40000 });
await page.waitForFunction(() => !!window.__boardDebug, { timeout: 25000 });
await page.waitForFunction(() => !!window.TASK_API, { timeout: 15000 }).catch(() => {});
await page.waitForTimeout(1500);

const state = await page.evaluate(() => {
  const counts = {};
  Object.entries(window.__boardDebug.ZONES || {}).forEach(([k, z]) => {
    if (z && z.tasks) counts[k] = z.tasks.length;
  });
  const total = Object.values(counts).reduce((a, b) => a + b, 0);
  const badge = document.getElementById('api-badge');
  const verifyTask = Object.values(window.__boardDebug.ZONES)
    .flatMap((z) => (z && z.tasks) || [])
    .find((t) => (t.source || '') === 'verify-api');
  return {
    apiActive: !!window.TASK_API,
    total, counts,
    badge: badge ? { cls: badge.className, text: badge.innerText, visible: getComputedStyle(badge).display } : null,
    verifyTask: verifyTask ? { id: verifyTask.id, dept: verifyTask.dept, status: verifyTask.status, api: !!verifyTask._api } : null,
    legend: Array.from(document.querySelectorAll('.legend-count')).map((e) => e.textContent.trim()).filter(Boolean).length,
  };
});
chk('看板识别到同源 API 并拉取', state.apiActive, `共 ${state.total} 条落到各房间`);
chk('新录任务出现在房间里', !!state.verifyTask,
  state.verifyTask ? `${state.verifyTask.dept} / ${state.verifyTask.status}` : '未找到');
chk('数据源指示灯为在线', state.badge && state.badge.cls === 'online', state.badge ? state.badge.text : '无');
chk('图例显示未完成/总数', state.legend > 0, `${state.legend} 个部门有计数`);

// ---------- ③ 看板 → 服务端回写 ----------
console.log('\n【3】看板操作回写服务端');
const target = state.verifyTask;
if (target) {
  const before = await (await fetch(`${BASE}/api/tasks?dept=${target.dept}`)).json();
  const b = before.tasks.find((t) => t.id === target.id) || { status: '(未取到)' };
  console.log(`  · 目标任务：${target.id}  当前 ${b.status}`);
  await page.evaluate(() => {
    // 直接点第一个房间卡片上的状态按钮（等价于用户操作）
    const dbg = window.__boardDebug;
    const zid = Object.keys(dbg.ZONES).find((k) => (dbg.ZONES[k].tasks || []).some((t) => (t.source || '') === 'verify-api'));
    if (zid) window.openPanel(zid);
  });
  await page.waitForTimeout(500);
  const clicked = await page.evaluate((tid) => {
    const btn = document.querySelector(`.task-status[data-task-id="${tid}"]`);
    if (!btn) return false;
    btn.click();
    return true;
  }, target.id);
  await page.waitForTimeout(1200);
  const after = await (await fetch(`${BASE}/api/tasks?dept=${target.dept}`)).json();
  const a = after.tasks.find((t) => t.id === target.id);
  chk('点状态按钮后服务端已更新', clicked && a && a.status !== b.status,
    clicked ? `${b.status} → ${a ? a.status : '?'}` : '按钮未找到');
}

// ---------- ④ 幂等 / 去重 ----------
console.log('\n【4】重复录入幂等（同一任务再发一次不应新增）');
const dupBody = JSON.stringify({ title: `接口验证-单条 ${stamp}`, dept: 'meeting', source: 'verify-api' });
const d1 = await (await fetch(BASE + '/api/tasks', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: dupBody })).json();
chk('重复录入只更新不新增', d1.added === 0 && d1.updated === 1, `added=${d1.added} updated=${d1.updated}`);

// ---------- ⑤ 跨源显式 ?api=（静态页 + 远端服务，验证 CORS） ----------
console.log('\n【5】显式 ?api= 模式（静态页指向远端服务）');
const STATIC = process.env.BOARD_STATIC || 'http://127.0.0.1:8934/office-3d-taskboard.html';
{
  const p2 = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  const e2 = [];
  p2.on('pageerror', (e) => e2.push(e.message));
  await p2.goto(`${STATIC}?api=${encodeURIComponent(BASE)}`, { waitUntil: 'domcontentloaded' });
  await p2.waitForFunction(() => !!window.__boardDebug, { timeout: 30000 });
  await p2.waitForTimeout(8000);
  const r = await p2.evaluate(() => {
    const t = window.TASK_API;
    if (!t) return { n: -1, badge: '' };
    const n = Object.values(t.buckets || {}).reduce((s, a) => s + a.length, 0) + (t.unassigned || []).length;
    return { n, badge: ((document.getElementById('api-badge') || {}).textContent || '').trim() };
  });
  chk('跨源显式指定后拉取到任务', r.n > 0, `共 ${r.n} 条`);
  chk('数据源指示灯为在线', r.badge.includes('实时同步'), r.badge);
  chk('跨源页面无 JS 错误', e2.length === 0, e2.join(' | ') || '无');
  await p2.close();
}

// ---------- ⑥ 清理 ----------
console.log('\n【6】清理验证数据');
const all = await (await fetch(BASE + '/api/tasks?source=verify-api')).json();
let del = 0;
for (const t of all.tasks) {
  const r = await fetch(BASE + '/api/tasks/' + encodeURIComponent(t.id), { method: 'DELETE' });
  if (r.ok) del++;
}
chk('删除验证任务', del === all.count, `删除 ${del}/${all.count} 条`);

await browser.close();
console.log('\n页面错误：', errs.length ? errs.join(' | ') : '无');
console.log('\n===== 结果：' + (fails === 0 ? '全部通过 ✅' : fails + ' 项未通过 ❌') + ' =====');
process.exit(fails === 0 ? 0 : 1);
