// v5.1 验收：① 门牌朝向 ② 地毯共面重叠 ③ 桌面模型清点 + 近景取图
import { chromium } from './node_modules/playwright/index.mjs';
import { rtShot, look } from './grab.mjs';
const BASE = 'http://127.0.0.1:8934/office-3d-taskboard.html';
const OUT = 'C:/Users/Perfect/Desktop/3d-taskboard-main/_shots/';
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe' });
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
await page.goto(BASE, { waitUntil: 'domcontentloaded' });
await page.waitForFunction(() => !!window.__boardDebug, { timeout: 20000 });
await page.waitForTimeout(16000);

const diag = await page.evaluate(async () => {
  const THREE = await import('three');
  const d = window.__boardDebug;
  const out = { plaques: [], rugSameYOverlap: [], roomShowItems: {} };

  // ① 门牌朝向
  for (const rg of d.scene.children.filter(o => o.isGroup && o.children.length >= 5)) {
    const inner = rg.children.find(c => c.isGroup && c.children.some(x => x.isMesh && x.geometry && x.geometry.type === 'BoxGeometry' && x.geometry.parameters && x.geometry.parameters.depth === 0.06));
    if (!inner) continue;
    const wp = new THREE.Vector3(), wq = new THREE.Quaternion();
    inner.updateWorldMatrix(true, false);
    inner.matrixWorld.decompose(wp, wq, new THREE.Vector3());
    const n = new THREE.Vector3(0, 0, 1).applyQuaternion(wq);
    const rp = rg.getWorldPosition(new THREE.Vector3());
    const o = new THREE.Vector3(wp.x - rp.x, 0, wp.z - rp.z).normalize();
    const dot = n.x * o.x + n.z * o.z;
    out.plaques.push({ at: [+wp.x.toFixed(2), +wp.z.toFixed(2)], dot: +dot.toFixed(3), ok: dot > 0.3 });
  }

  // ② 地毯：y 接近且 x/z 相交 = 共面闪烁
  const rugs = [];
  d.scene.traverse(o => {
    if (o.isMesh && o.geometry && o.geometry.type === 'PlaneGeometry') {
      const bb = new THREE.Box3().setFromObject(o);
      if (bb.min.y > 0.05 && bb.min.y < 0.14) rugs.push({ y: +bb.min.y.toFixed(3), x: [bb.min.x, bb.max.x], z: [bb.min.z, bb.max.z] });
    }
  });
  for (let i = 0; i < rugs.length; i++) for (let j = i + 1; j < rugs.length; j++) {
    const ox = Math.min(rugs[i].x[1], rugs[j].x[1]) - Math.max(rugs[i].x[0], rugs[j].x[0]);
    const oz = Math.min(rugs[i].z[1], rugs[j].z[1]) - Math.max(rugs[i].z[0], rugs[j].z[0]);
    if (ox > 0.01 && oz > 0.01 && Math.abs(rugs[i].y - rugs[j].y) < 0.002)
      out.rugSameYOverlap.push({ ox: +ox.toFixed(2), oz: +oz.toFixed(2), y: rugs[i].y });
  }

  // ③ 各房 GLB 件数（确认 office_monitor / laptop 已清空）
  const NAMES = ['office_monitor', 'laptop', 'exec_desk', 'exec_chair', 'office_chair', 'sofa', 'coffee_table', 'filing_cabinet', 'plant_potted'];
  const rooms = d.scene.children.filter(o => o.isGroup && o.position.x > 0 && o.position.z > 0 && o.children.length >= 5);
  rooms.forEach((rg, i) => {
    let cnt = 0;
    rg.traverse(o => { if (o.isGroup && o.parent && o.parent.isGroup) cnt++; });
    out.roomShowItems['room' + i] = cnt;
  });
  return out;
});
console.log('门牌：' + JSON.stringify(diag.plaques));
console.log('同 y 地毯重叠：' + JSON.stringify(diag.rugSameYOverlap));
console.log('各房 holder 数：' + JSON.stringify(diag.roomShowItems));

const VIEWS = [
  ['v0_overview', [14.8, 20.6, 30.4], [14.8, 0, 10.8]],
  ['v1_cro_desk', [13.45, 1.55, 5.60], [12.35, 0.88, 4.30]],
  ['v2_ceo_desk', [22.70, 1.55, 13.05], [21.80, 0.88, 14.60]],
  ['v3_cfo_desk', [5.00, 1.55, 18.45], [3.35, 0.88, 19.35]],
  ['v4_cfo_rugs', [5.40, 7.00, 21.00], [5.40, 0.00, 18.60]],
  ['v5_cfo_plaque', [11.40, 2.10, 17.50], [8.74, 2.35, 17.50]],
  ['v6_meeting_plaque', [10.60, 2.10, 15.20], [7.54, 2.35, 15.20]],
  ['v7_cpo_plaque', [9.60, 2.10, 7.40], [6.74, 2.35, 7.40]],
  ['v8_cmo_desks', [19.60, 2.05, 4.35], [19.50, 0.85, 2.20]],
  ['v9_cto_desk', [27.30, 1.55, 4.20], [26.70, 0.88, 3.60]],
  ['v10_coo_desk', [16.30, 1.55, 15.40], [15.70, 0.88, 14.70]],
  ['v11_cpo_desk', [4.90, 1.55, 8.90], [3.70, 0.88, 8.30]],
];
for (const [n, cam, tgt] of VIEWS) { await look(page, ...cam, ...tgt); await rtShot(page, OUT + n + '.png'); console.log('  ✓', n); }
await browser.close();
