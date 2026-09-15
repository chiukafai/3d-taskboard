// 修复后浏览器侧回归：JS 报错捕获 + 8 间房模型加载 + 门状态 + 关键视角重渲
import { chromium } from './node_modules/playwright/index.mjs';

const BASE = 'http://127.0.0.1:8934/office-3d-taskboard.html';
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe' });
const page = await browser.newPage({ viewport: { width: 1400, height: 900 }, deviceScaleFactor: 1.2 });

const errors = [], loads = [];
page.on('pageerror', e => errors.push('PAGEERROR: ' + e.message));
page.on('console', m => {
  const t = m.text();
  if (m.type() === 'error') errors.push('CONSOLE-ERR: ' + t);
  if (t.includes('样板房已加载')) loads.push(t);
});

await page.goto(BASE, { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(13000);

console.log('=== JS 报错 ===');
console.log(errors.length ? errors.join('\n') : '   ✅ 无报错');
console.log('\n=== 房间模型加载 ===');
loads.forEach(l => console.log('  ', l));
console.log(`   合计 ${loads.length}/8 间`);

await page.evaluate(() => {
  ['toolbar', 'panel', 'legend', 'hint', 'syspanel', 'loading'].forEach(id => { const e = document.getElementById(id); if (e) e.style.display = 'none'; });
  document.querySelectorAll('div').forEach(d => { const t = (d.textContent || '').trim(); if (t.startsWith('加载')) d.style.display = 'none'; });
});

const views = [
  { n: 'f1_plan_top',   cam: [12, 48, 9.01],  tgt: [12, 0, 9],    fov: 30 },
  { n: 'f2_overview',   cam: [36, 22, 34],    tgt: [12, 0, 9],    fov: 42 },
  { n: 'f3_hall_north', cam: [12, 4.5, 10.5], tgt: [12, 1.6, 5],  fov: 62 },
  { n: 'f4_hall_south', cam: [12, 4.5, 7.5],  tgt: [12, 1.6, 13], fov: 62 },
  { n: 'f5_cpo_room',   cam: [21, 3.4, 9.0],  tgt: [21, 1.4, 3],  fov: 55 },
  { n: 'f6_coo_room',   cam: [8.5, 3.4, 9.0], tgt: [8.5, 1.4, 3], fov: 55 },
  { n: 'f7_ceo_room',   cam: [12, 3.4, 10.0], tgt: [12, 1.4, 16], fov: 55 },
  { n: 'f8_cfo_room',   cam: [20, 3.4, 10.0], tgt: [20, 1.4, 16], fov: 55 },
];
for (const v of views) {
  await page.evaluate(({ cam, tgt, fov }) => {
    const d = window.__boardDebug;
    d.camera.fov = fov; d.camera.updateProjectionMatrix();
    d.camera.position.set(cam[0], cam[1], cam[2]);
    d.controls.target.set(tgt[0], tgt[1], tgt[2]);
    d.controls.update();
  }, v);
  await page.waitForTimeout(700);
  await page.screenshot({ path: `../_shots/${v.n}.png` });
}
console.log('\n=== 截图 ===');
views.forEach(v => console.log('   已存 _shots/' + v.n + '.png'));

const doors = await page.evaluate(() => Object.entries(window.__boardDebug.doorGroups).map(([k, p]) => {
  const w = p.getWorldPosition(new p.position.constructor());
  return `${k} @(${w.x.toFixed(1)},${w.z.toFixed(1)})`;
}));
console.log('\n=== 门 ===');
doors.forEach(d => console.log('  ', d));
await browser.close();
