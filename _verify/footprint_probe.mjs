// 场景足印探测：对采样网格从高空垂直打射线 → 直接得到 3D 场景的"有实体"分布
// 完全绕开渲染/截图（画布 alpha、页面背景、抗锯齿都不会干扰），结果确定可复现。
import { chromium } from './node_modules/playwright/index.mjs';
import fs from 'fs';
const BASE = 'http://127.0.0.1:8934/office-3d-taskboard.html';
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe' });
const page = await browser.newPage({ viewport: { width: 900, height: 700 } });
await page.goto(BASE, { waitUntil: 'domcontentloaded' });
await page.waitForFunction(() => !!window.__boardDebug, { timeout: 20000 });
await page.waitForTimeout(13000);

const res = await page.evaluate(async () => {
  const THREE = await import('three');
  const d = window.__boardDebug;
  // 排除室外大地面（96×96 草地）：它覆盖全图，会把一切判为"有实体"
  const ground = [];
  d.scene.traverse(o => {
    if (o.isMesh && o.geometry?.type === 'PlaneGeometry' && (o.geometry.parameters?.width || 0) >= 50) ground.push(o);
  });
  ground.forEach(o => o.visible = false);
  const rc = new THREE.Raycaster();
  rc.far = 400;
  const G = 0.2;                                   // 采样格 0.2m
  const NX = Math.round(29.6 / G) + 1, NZ = Math.round(21.6 / G) + 1;
  const grid = [];
  for (let j = 0; j < NZ; j++) {
    const row = [];
    for (let i = 0; i < NX; i++) {
      const x = i * G, z = j * G;
      rc.set(new THREE.Vector3(x, 100, z), new THREE.Vector3(0, -1, 0));
      const hits = rc.intersectObjects(d.scene.children, true)
        .filter(h => h.object.isMesh && h.object.visible);
      row.push(hits.length ? 1 : 0);
    }
    grid.push(row);
  }
  ground.forEach(o => o.visible = true);
  return { G, NX, NZ, grid };
});
fs.writeFileSync('_footprint.json', JSON.stringify(res));
console.log(`足印网格 ${res.NX}×${res.NZ} @ ${res.G}m  → _verify/_footprint.json`);

// 直接打一份粗 ASCII（0.4m 抽稀）
const step = 2;
console.log('\n   x: 0 → 29.6  (每列 %.1fm)' % 0);
for (let j = 0; j < res.NZ; j += step) {
  let s = '';
  for (let i = 0; i < res.NX; i += step) s += res.grid[j][i] ? '#' : '.';
  console.log(`z=${(j * res.G).toFixed(1).padStart(5)} ${s}`);
}
await browser.close();
