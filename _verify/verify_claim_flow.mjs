// 端到端验证：A+B 中间态「建议认领 + 人工确认」闭环
//
// 要证明的核心不是"接口能通"，而是这条纪律成立：
//   **agent 只能提建议，改不动任务状态；人不点批准，活就不会被领走。**
//
// 用法: node verify_claim_flow.mjs [base]   默认 http://127.0.0.1:8787
import { chromium } from 'playwright';

const BASE = (process.argv[2] || 'http://127.0.0.1:8787').replace(/\/+$/, '');
const ok = (b) => (b ? '✅' : '❌');
let fails = 0;
const chk = (label, pass, extra = '') => {
  if (!pass) fails++;
  console.log(`  ${ok(pass)} ${label}${extra ? '  — ' + extra : ''}`);
};
const j = async (url, init) => (await fetch(url, init)).json();
const post = (url, body) =>
  fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });

console.log('===== 认领闭环（A+B 中间态）验证 =====');
console.log('BASE =', BASE, '\n');

const SRC = 'claim-test';
const AG1 = 'claude-code';
const AG2 = 'hermes';
const stamp = new Date().toISOString().slice(11, 19);

// ---------- ① 准备：两条待办任务 ----------
console.log('【1】准备两条待办任务');
await j(BASE + '/api/tasks', {
  method: 'POST', headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify([
    { title: `认领验证-甲 ${stamp}`, dept: 'cfo', status: 'todo', priority: 'high', source: SRC },
    { title: `认领验证-乙 ${stamp}`, dept: 'meeting', status: 'todo', source: SRC },
  ]),
});
const mine = (await j(`${BASE}/api/tasks?source=${SRC}`)).tasks;
const tA = mine.find((t) => t.title.includes('甲'));
const tB = mine.find((t) => t.title.includes('乙'));
chk('两条待办已入库', !!tA && !!tB, `${tA?.id} / ${tB?.id}`);
chk('新任务初始无认领', tA && tA.claim_state === 'none' && tA.assignee === '', `claim_state=${tA?.claim_state}`);

// ---------- ② agent 提建议认领 ----------
console.log('\n【2】agent 只能"提建议"，改不动状态');
const p1 = await (await post(`${BASE}/api/tasks/${tA.id}/claim`, { agent: AG1, note: '这块我熟' })).json();
chk('POST /api/tasks/<id>/claim 登记意向', p1.ok === true && p1.claim.status === 'proposed',
  `result=${p1.result}`);
const p2 = await (await post(`${BASE}/api/tasks/${tA.id}/claim`, { agent: AG2, note: '我也可以' })).json();
chk('第二个 agent 也能排队申请', p2.ok === true, `result=${p2.result}`);

const stillTodo = (await j(`${BASE}/api/tasks?claim=pending`)).tasks.find((t) => t.id === tA.id);
chk('★ 关键：任务状态仍是 todo（agent 无权自行开工）', stillTodo && stillTodo.status === 'todo',
  `status=${stillTodo?.status}`);
chk('★ 关键：任务无 assignee', stillTodo && !stillTodo.assignee, `assignee="${stillTodo?.assignee}"`);
chk('待批申请数为 2', stillTodo && stillTodo.claim_pending === 2, `claim_pending=${stillTodo?.claim_pending}`);

const proposed = (await j(`${BASE}/api/claims?status=proposed`)).claims.filter((c) => c.task_id === tA.id);
chk('GET /api/claims?status=proposed 可列待批', proposed.length === 2,
  proposed.map((c) => c.agent).join(','));
const cA = proposed.find((c) => c.agent === AG1);
const cB = proposed.find((c) => c.agent === AG2);

const q0 = await j(`${BASE}/api/queue?agent=${AG1}`);
chk('批准前 queue 为空（拿不到活）', q0.count === 0, `count=${q0.count}`);

// ---------- ③ 已批准后再申请不应被劫持 ----------
console.log('\n【3】认领的排他性');
const other = await fetch(`${BASE}/api/tasks/${tB.id}/claim`, {
  method: 'POST', headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ agent: AG1, note: 'x' }),
});
await other.json();
const apB = await (await post(`${BASE}/api/claims/${(await j(`${BASE}/api/claims?task=${tB.id}`)).claims[0].id}/approve`,
  { by: 'verify' })).json();
chk('批准后任务转为进行中并落定执行方', apB.task?.status === 'in_progress' && apB.task?.assignee === AG1,
  `${apB.task?.status} / ${apB.task?.assignee}`);
const grab = await fetch(`${BASE}/api/tasks/${tB.id}/claim`, {
  method: 'POST', headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ agent: 'openai-codex' }),
});
chk('★ 已被认领后再抢 → 409', grab.status === 409, `HTTP ${grab.status}`);

// ---------- ④ 看板端显示与人工放行 ----------
console.log('\n【4】看板：看得见 + 点一下就放行');
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
await page.waitForFunction(() => !!window.TASK_API, { timeout: 20000 }).catch(() => {});
await page.waitForTimeout(1500);

const ui = await page.evaluate(() => {
  const badge = document.getElementById('claim-badge');
  return {
    badgeVisible: badge && getComputedStyle(badge).display !== 'none',
    badgeText: (badge || {}).textContent || '',
    pending: window.collectClaims('proposed').length,
    zones: window.collectClaims('proposed').map((x) => x.zoneId),
  };
});
chk('看板识别到待批认领', ui.badgeVisible && ui.pending > 0, `${ui.badgeText} · 共 ${ui.pending} 条`);

// 展开左下角浮层，核对"人看到的东西"确实列出来了
const tray = await page.evaluate(() => {
  window.toggleClaimTray(true);
  const el = document.getElementById('claim-tray');
  return {
    visible: getComputedStyle(el).display !== 'none',
    rows: el.querySelectorAll('.claim-row').length,
    agents: Array.from(el.querySelectorAll('.claim-row .cl-agent')).map((e) => e.textContent.trim()),
    hasButtons: !!el.querySelector('button[data-approve="1"]'),
  };
});
chk('认领浮层可展开并列出待批', tray.visible && tray.rows >= 1,
  `${tray.rows} 行：${tray.agents.join(', ')}`);
chk('浮层里有「批准/驳回」按钮', tray.hasButtons);
await page.evaluate(() => window.toggleClaimTray(false));

// 必须开 tA 自己所在的房间，否则卡片根本不在 DOM 里
const zoneA = (await j(`${BASE}/api/tasks?source=${SRC}`)).tasks.find((t) => t.id === tA.id).dept;
await page.evaluate((z) => window.openPanel(z), zoneA);
await page.waitForTimeout(700);
const card = await page.evaluate((tid) => {
  const badge = document.querySelector(`.task-card[data-task-id="${tid}"] .task-claim.pending`);
  const approve = document.querySelector(`.task-action-btn[data-action="claim-approve"][data-task-id="${tid}"]`);
  return { badge: badge ? badge.textContent.trim() : null, hasApprove: !!approve };
}, tA.id);
chk('任务卡上出现「🔔 待批」徽标', !!card.badge, card.badge || '未渲染');
chk('任务卡上有「✓ 批准」按钮', card.hasApprove);

// 点 ✓ → 走真实用户路径。
// 注意：这条任务有 2 个申请人，卡片上的 ✓ **不会替用户选人**，而是展开浮层让人挑。
const clicked = await page.evaluate((tid) => {
  const b = document.querySelector(`.task-action-btn[data-action="claim-approve"][data-task-id="${tid}"]`);
  if (!b) return false;
  b.click();
  return true;
}, tA.id);
await page.waitForTimeout(400);
const trayAfterClick = await page.evaluate(() => {
  const el = document.getElementById('claim-tray');
  return { visible: getComputedStyle(el).display !== 'none', rows: el.querySelectorAll('.claim-row').length };
});
chk('多申请人时点 ✓ → 展开浮层让人挑（不替用户决定）',
  clicked && trayAfterClick.visible && trayAfterClick.rows >= 2, `${trayAfterClick.rows} 行`);

// 在浮层里批准 claude-code 那条
const trayClicked = await page.evaluate((cid) => {
  const b = document.querySelector(`#claim-tray button[data-claim-id="${cid}"][data-approve="1"]`);
  if (!b) return false;
  b.click();
  return true;
}, cA.id);
await page.waitForTimeout(2000);
const afterApprove = (await j(`${BASE}/api/tasks?source=${SRC}`)).tasks.find((t) => t.id === tA.id);
chk('★ 看板点「批准」后服务端已放行', trayClicked && afterApprove.status === 'in_progress'
  && afterApprove.assignee === AG1, `${afterApprove?.status} / ${afterApprove?.assignee}`);

const siblings = (await j(`${BASE}/api/claims?task=${tA.id}`)).claims;
const loser = siblings.find((c) => c.agent === AG2);
chk('同任务其它申请被自动驳回', loser && loser.status === 'rejected', `hermes → ${loser?.status}（${loser?.reason}）`);

// ---------- ⑤ agent 取队列并回报 ----------
console.log('\n【5】agent 取「已批准的活」并回报');
const q1 = await j(`${BASE}/api/queue?agent=${AG1}`);
chk('GET /api/queue?agent= 拿到可开工任务', q1.count >= 1 && q1.tasks.some((t) => t.id === tA.id),
  `${q1.count} 条：${q1.tasks.map((t) => t.title).join(', ')}`);
const q2 = await j(`${BASE}/api/queue?agent=${AG2}`);
chk('落选 agent 队列为空（不会两人同时开工）', !q2.tasks.some((t) => t.id === tA.id), `count=${q2.count}`);

// 回归锁：曾经有过"已批准的申请被自己再报一次就退回待批"的 bug（等于绕过人工关口）
const reClaim = await (await post(`${BASE}/api/tasks/${tB.id}/claim`, { agent: AG1, note: '补充说明' })).json();
const tBAfter = (await j(`${BASE}/api/tasks?source=${SRC}`)).tasks.find((t) => t.id === tB.id);
chk('★ 已批准的申请再报一次 → 不退回待批', reClaim.result === 'already_approved' && tBAfter.assignee === AG1,
  `result=${reClaim.result} assignee="${tBAfter?.assignee}"`);

await post(`${BASE}/api/tasks`, { title: tA.title, dept: 'cfo', status: 'done', source: SRC });
const doneT = (await j(`${BASE}/api/tasks?source=${SRC}`)).tasks.find((t) => t.id === tA.id);
chk('agent 回报完成（status=done）', doneT.status === 'done', `status=${doneT.status}`);
// 已完成的任务再申请应被明确拒绝；已批准的任务再报一次也不能退回待批
const doneClaim = await (await post(`${BASE}/api/tasks/${tA.id}/claim`, { agent: AG1, note: '再报一次' })).json();
chk('★ 已批准/已完成的任务不会被"再申请"劫持', doneClaim.ok === false || doneClaim.result === 'already_approved',
  `ok=${doneClaim.ok} result=${doneClaim.result || doneClaim.error}`);

// ---------- ⑥ 撤销认领 ----------
console.log('\n【6】撤销认领（人要能收回放行）');
const revClaim = (await j(`${BASE}/api/claims?task=${tB.id}`)).claims.find((c) => c.status === 'approved');
const rv = await (await post(`${BASE}/api/claims/${revClaim.id}/reject`, { by: 'verify', reason: '撤销' })).json();
chk('撤销后任务退回待办', rv.task?.status === 'todo', `status=${rv.task?.status}`);
chk('撤销后执行方已清空', !rv.task?.assignee, `assignee="${rv.task?.assignee}"`);

// 只有 1 个申请人时，卡片上的 ✓ 应当直接批准（不需要再展开浮层）
// 注意：看板默认 20 秒轮询一次，外部 agent 刚提的申请要等下一轮才到页面 ——
// 这里用刷新代替等待，顺便也验证了"刷新后依然能正常审批"。
const solo = await (await post(`${BASE}/api/tasks/${tB.id}/claim`, { agent: AG2, note: '一个人申请' })).json();
chk('重新申请后回到待批', ['proposed', 'reproposed'].includes(solo.result), `result=${solo.result}`);
const zoneB = (await j(`${BASE}/api/tasks?source=${SRC}`)).tasks.find((t) => t.id === tB.id).dept;
await page.reload({ waitUntil: 'load', timeout: 40000 });
await page.waitForFunction(() => !!window.TASK_API, { timeout: 20000 });
await page.evaluate((z) => window.openPanel(z), zoneB);
await page.waitForTimeout(900);
const soloClicked = await page.evaluate((tid) => {
  const b = document.querySelector(`.task-action-btn[data-action="claim-approve"][data-task-id="${tid}"]`);
  if (!b) return false;
  b.click();
  return true;
}, tB.id);
await page.waitForTimeout(2200);
const tBfinal = (await j(`${BASE}/api/tasks?source=${SRC}`)).tasks.find((t) => t.id === tB.id);
chk('唯一申请人时点 ✓ → 直接批准', soloClicked && tBfinal.assignee === AG2,
  `assignee="${tBfinal?.assignee}" status=${tBfinal?.status}`);

// ---------- ⑦ CLI 侧一致性 ----------
console.log('\n【7】CLI 与 API 共用同一份真相');
const claimsCli = await j(`${BASE}/api/claims?task=${tB.id}`);
chk('撤销痕迹保留（可审计，不删记录）', claimsCli.claims.some((c) => c.status === 'rejected'),
  claimsCli.claims.map((c) => `${c.agent}:${c.status}`).join(' '));

// ---------- ⑧ 清理 ----------
console.log('\n【8】清理验证数据');
const cleanup = (await j(`${BASE}/api/tasks?source=${SRC}`)).tasks;
let del = 0;
for (const t of cleanup) {
  const r = await fetch(`${BASE}/api/tasks/${encodeURIComponent(t.id)}`, { method: 'DELETE' });
  if (r.ok) del++;
}
chk('删除验证任务', del === cleanup.length, `${del}/${cleanup.length}`);
const leftClaims = (await j(`${BASE}/api/claims`)).claims.filter((c) => [tA.id, tB.id].includes(c.task_id));
chk('任务删除后认领记录一并清理', leftClaims.length === 0, `${leftClaims.length} 条残留`);

await browser.close();
console.log('\n页面错误：', errs.length ? errs.join(' | ') : '无');
console.log('\n===== 结果：' + (fails === 0 ? '全部通过 ✅' : fails + ' 项未通过 ❌') + ' =====');
process.exit(fails === 0 ? 0 : 1);
