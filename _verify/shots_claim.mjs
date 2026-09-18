/* 认领功能截图留档：徽标 / 浮层 / 卡片按钮
   用法：node shots_claim.mjs [base]   默认 http://127.0.0.1:8787 */
import { chromium } from './node_modules/playwright/index.mjs';

const BASE = (process.argv[2] || 'http://127.0.0.1:8787').replace(/\/+$/, '');
const OUT = '../_shots';
const b = await chromium.launch({
  headless: true,
  executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
  args: ['--no-sandbox', '--disable-dev-shm-usage'],
});
const p = await (await b.newContext({ viewport: { width: 1560, height: 960 } })).newPage();
await p.goto(BASE + '/office-3d-taskboard.html', { waitUntil: 'load', timeout: 40000 });
await p.waitForFunction(() => !!window.__boardDebug, { timeout: 25000 });
await p.waitForFunction(() => !!window.TASK_API, { timeout: 20000 }).catch(() => {});
await p.waitForTimeout(2500);
await p.evaluate(() => document.getElementById('hint')?.style.setProperty('display', 'none'));

// ① 总览：左下角出现「🔔 N 条认领待批」
await p.screenshot({ path: `${OUT}/claim_1_badge.png` });
console.log('① claim_1_badge.png      左下角 🔔 徽标');

// ② 展开认领浮层
const n = await p.evaluate(() => {
  const el = document.getElementById('claim-badge');
  if (!el || getComputedStyle(el).display === 'none') return 0;
  el.click();
  return document.querySelectorAll('#claim-tray .claim-row').length;
});
if (n) {
  await p.waitForTimeout(600);
  await p.screenshot({ path: `${OUT}/claim_2_tray.png` });
  console.log(`② claim_2_tray.png       浮层里 ${n} 条待批申请（含理由 + 批准/驳回）`);
} else {
  console.log('② 跳过：当前没有待批认领（跑 python -m taskboard seed-demo 造一条）');
}

// ③ 任务卡上的徽标 + ✓/✕ 按钮
const zone = await p.evaluate(() => {
  const hit = window.collectClaims('proposed')[0];
  return hit ? hit.zoneId : null;
});
if (zone) {
  await p.evaluate((z) => { window.toggleClaimTray(false); window.openPanel(z); }, zone);
  await p.waitForTimeout(800);
  const found = await p.evaluate(() =>
    !!document.querySelector('.task-card .task-claim.pending') &&
    !!document.querySelector('.task-action-btn[data-action="claim-approve"]'));
  await p.screenshot({ path: `${OUT}/claim_3_card.png` });
  console.log(`③ claim_3_card.png       卡片上的「🔔 待批」徽标与 ✓/✕ 按钮：${found ? '已渲染' : '未找到'}`);
}

// ④ 部门待核标记（引擎猜出来的部门）
const guessZone = await p.evaluate(() => {
  const z = Object.values(window.__boardDebug.ZONES)
    .find((z) => (z.tasks || []).some((t) => t.dept_source === 'guessed'));
  return z ? z.id : null;
});
if (guessZone) {
  await p.evaluate((z) => window.openPanel(z), guessZone);
  await p.waitForTimeout(700);
  await p.screenshot({ path: `${OUT}/claim_4_guess.png` });
  console.log('④ claim_4_guess.png      猜出来的部门被打「部门待核」灰标');
}

await b.close();
