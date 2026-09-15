// 重排后视觉验证：平面图 + 大厅南北视角 + 3 处原问题点特写
import { chromium } from './node_modules/playwright/index.mjs';

const BASE = 'http://127.0.0.1:8934/office-3d-taskboard.html';
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe' });
const page = await browser.newPage({ viewport: { width: 1400, height: 900 }, deviceScaleFactor: 1.2 });
await page.goto(BASE, { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(12000);

// 隐藏 UI 遮挡
await page.evaluate(() => {
  ['toolbar', 'panel', 'legend', 'hint', 'syspanel', 'loading'].forEach(id => {
    const e = document.getElementById(id); if (e) e.style.display = 'none';
  });
  document.querySelectorAll('div').forEach(d => {
    const t = (d.textContent || '').trim();
    if (t.startsWith('加载') || t.startsWith('Loading')) d.style.display = 'none';
  });
});

const views = [
  { n: 'v1_plan_top',    cam: [12, 46, 9.01],   tgt: [12, 0, 9],    fov: 30 },
  { n: 'v2_overview_se', cam: [34, 20, 32],     tgt: [12, 0, 9],    fov: 42 },
  { n: 'v3_hall_north',  cam: [12, 4.5, 10.5],  tgt: [12, 1.6, 5],  fov: 62 },
  { n: 'v4_hall_south',  cam: [12, 4.5, 7.5],   tgt: [12, 1.6, 13], fov: 62 },
  { n: 'v5_cpo_door',    cam: [21, 3.2, 9.5],   tgt: [21, 1.5, 5],  fov: 52 },
  { n: 'v6_cfo_door',    cam: [20, 3.2, 11.5],  tgt: [20, 1.5, 15], fov: 52 },
  { n: 'v7_cmo_east',    cam: [19, 3.5, 9],     tgt: [24, 1.5, 9],  fov: 60 },
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
  console.log('saved', v.n);
}

// 门交互状态确认
const doors = await page.evaluate(() => {
  const d = window.__boardDebug;
  return Object.entries(d.doorGroups).map(([k, p]) => ({
    k, open: !!p.userData.opened, rotY: +p.rotation.y.toFixed(3),
    x: +p.getWorldPosition(new p.position.constructor()).x.toFixed(2),
    z: +p.getWorldPosition(new p.position.constructor()).z.toFixed(2),
  }));
});
console.log('=== doors ===');
doors.forEach(r => console.log(' ', r.k, 'open=' + r.open, 'rotY=' + r.rotY, `@(${r.x},${r.z})`));

await browser.close();
