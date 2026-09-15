// v4 视觉复核：正投影俯视图 + 全景 + 8 房 + 接待厅 + 入口前庭
import { chromium } from './node_modules/playwright/index.mjs';
import fs from 'fs';
const BASE = 'http://127.0.0.1:8934/office-3d-taskboard.html';
const OUT = 'C:/Users/Perfect/Desktop/3d-taskboard-main/_shots/';
fs.mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe' });
const page = await browser.newPage({ viewport: { width: 1400, height: 1000 } });
await page.goto(BASE, { waitUntil: 'domcontentloaded' });
await page.waitForFunction(() => !!window.__boardDebug, { timeout: 20000 });
await page.waitForTimeout(14000);

const zones = ['cpo', 'meeting', 'cfo', 'cro', 'cmo', 'cto', 'coo', 'ceo'];

// ── 1) 正交俯视图（与平面图 v4 直接对位比较）──
await page.evaluate(async () => {
  const THREE = await import('three');
  const d = window.__boardDebug;
  d.scene.fog = null;
  const w = 31.6, h = 23.6;                    // 包络 29.6×21.6 + 余量
  const cam = new THREE.OrthographicCamera(-w / 2, w / 2, h / 2, -h / 2, 0.1, 200);
  cam.position.set(14.8, 60, 10.8);
  cam.up.set(0, 0, -1);
  cam.lookAt(14.8, 0, 10.8);
  cam.updateProjectionMatrix();
  d.__cam = d.camera;
  window.__renderWith = cam;
  if (!window.__origRender) {
    window.__origRender = d.renderer.render.bind(d.renderer);
    d.renderer.render = (sc, c) => window.__origRender(sc, window.__renderWith || c);
  }
  for (const z of Object.keys(d.ZONES)) if (d.doorGroups[z]) d.openDoor(z, false);
});
await page.waitForTimeout(1200);
await page.screenshot({ path: OUT + 'p1_plan_top.png' });

// 门全开的俯视，检查门扇朝外扫出
await page.evaluate(() => { const d = window.__boardDebug; for (const z of Object.keys(d.ZONES)) if (d.doorGroups[z]) d.openDoor(z, true); });
await page.waitForTimeout(1800);
await page.screenshot({ path: OUT + 'p2_plan_doors_open.png' });

// ── 2) 恢复透视相机 ──
await page.evaluate(() => { window.__renderWith = null; const d = window.__boardDebug; for (const z of Object.keys(d.ZONES)) if (d.doorGroups[z]) d.openDoor(z, false); });
await page.waitForTimeout(1500);
await page.screenshot({ path: OUT + 'p3_overview.png' });

// ── 3) 接待厅 / 入口前庭近景 ──
const views = [
  ['p4_lobby', 9.4, 4.2, 17.0, 9.4, 0.6, 10.8],
  ['p5_forecourt', 6.0, 4.0, -2.5, 4.0, 0.4, 4.0],
  ['p6_corridor', 6.0, 5.5, 26.0, 17.0, 0.6, 10.0],
  ['p7_eastyard', 33.0, 4.5, 20.5, 27.5, 0.5, 15.5],
];
for (const [name, px, py, pz, lx, ly, lz] of views) {
  await page.evaluate(([px, py, pz, lx, ly, lz]) => {
    const d = window.__boardDebug;
    d.camera.position.set(px, py, pz);
    d.controls.target.set(lx, ly, lz);
    d.camera.lookAt(lx, ly, lz);
    d.controls.update();
  }, [px, py, pz, lx, ly, lz]);
  await page.waitForTimeout(900);
  await page.screenshot({ path: OUT + name + '.png' });
}

// ── 4) 8 房逐一（用 ?zone= 自动聚焦）──
for (const z of zones) {
  await page.goto(`${BASE}?zone=${z}`, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => !!window.__boardDebug, { timeout: 15000 });
  await page.waitForTimeout(9000);
  await page.screenshot({ path: OUT + `p8_${z}.png` });
}

const list = fs.readdirSync(OUT).filter(f => f.startsWith('p') && f.endsWith('.png')).sort();
console.log('=== 截图产物 ===');
list.forEach(f => console.log(`  ${f.padEnd(26)} ${(fs.statSync(OUT + f).size / 1024).toFixed(0)} KB`));
await browser.close();
