// 看板「实时数据源」截图留档（面板 + 俯视 + 局部）
import { chromium } from 'playwright';
const BASE = process.argv[2] || 'http://127.0.0.1:8787';
const OUT = 'C:/Users/Perfect/Desktop/3d-taskboard-main/_shots';
const browser = await chromium.launch({
  headless: true,
  executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
  args: ['--no-sandbox', '--disable-dev-shm-usage'],
});
const page = await (await browser.newContext({ viewport: { width: 1500, height: 940 } })).newPage();
await page.goto(BASE + '/office-3d-taskboard.html', { waitUntil: 'load', timeout: 40000 });
await page.waitForFunction(() => !!window.__boardDebug, { timeout: 25000 });
await page.waitForFunction(() => !!window.TASK_API, { timeout: 15000 }).catch(() => {});
await page.waitForTimeout(2500);

// ① 总览
await page.evaluate(() => { window.__boardDebug.animateToOverview && window.__boardDebug.animateToOverview(); });
await page.waitForTimeout(1800);
await page.screenshot({ path: OUT + '/taskboard_overview.png' });

// ② 打开一个部门的侧栏（看任务卡片的来源标签）
await page.evaluate(() => window.openPanel('cfo'));
await page.waitForTimeout(1600);
await page.screenshot({ path: OUT + '/taskboard_panel_cfo.png' });
await page.evaluate(() => window.closePanel && window.closePanel());
await page.waitForTimeout(600);

// ③ 中控台（未归类任务会出现在「记忆派生任务」区）
await page.evaluate(() => { const b = document.getElementById('btn-sys'); if (b) b.click(); });
await page.waitForTimeout(1000);
await page.screenshot({ path: OUT + '/taskboard_syspanel_api.png' });

const info = await page.evaluate(() => {
  const d = window.__boardDebug;
  const counts = {};
  Object.entries(d.ZONES).forEach(([k, z]) => { if (z && z.tasks && z.tasks.length) counts[k] = z.tasks.length; });
  const badge = document.getElementById('api-badge');
  return {
    total: Object.values(d.ZONES).reduce((a, z) => a + ((z && z.tasks) ? z.tasks.length : 0), 0),
    counts,
    api: !!window.TASK_API,
    badge: badge ? badge.innerText : '(无)',
    unassigned: ((window.TASK_DATA && window.TASK_DATA['_unassigned']) || []).length,
    sources: Array.from(new Set(Object.values(d.ZONES).flatMap(z => ((z && z.tasks) || []).map(t => t.source).filter(Boolean)))),
  };
});
await browser.close();
console.log(JSON.stringify(info, null, 1));
