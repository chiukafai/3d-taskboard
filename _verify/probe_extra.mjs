// 定位"渲染多出"的区域：对差异点从高空垂直打射线，看命中的是什么物体
import { chromium } from './node_modules/playwright/index.mjs';
const BASE = 'http://127.0.0.1:8934/office-3d-taskboard.html';
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe' });
const page = await browser.newPage({ viewport: { width: 900, height: 700 } });
await page.goto(BASE, { waitUntil: 'domcontentloaded' });
await page.waitForFunction(() => !!window.__boardDebug, { timeout: 20000 });
await page.waitForTimeout(13000);

const pts = [
  [11.0, 0.2], [13.0, 0.2], [15.0, 0.2], [9.0, 0.2],
  [14.0, 21.5], [17.0, 21.5], [28.5, 20.5], [28.5, 21.5],
  [28.5, 18.0], [12.0, 12.0], [9.4, 10.8], [24.0, 10.0],
];
const out = await page.evaluate(async (pts) => {
  const THREE = await import('three');
  const d = window.__boardDebug;
  const rc = new THREE.Raycaster();
  const res = [];
  for (const [x, z] of pts) {
    rc.set(new THREE.Vector3(x, 60, z), new THREE.Vector3(0, -1, 0));
    const hits = rc.intersectObjects(d.scene.children, true).filter(h => h.object.isMesh && h.object.visible);
    const h = hits[0];
    if (!h) { res.push({ x, z, hit: '空' }); continue; }
    const o = h.object;
    const p = o.geometry.parameters || {};
    const c = o.material?.color ? '#' + o.material.color.getHexString() : '?';
    let chain = [], n = o;
    while (n && n !== d.scene) { chain.push(n.name || n.type); n = n.parent; }
    res.push({
      x, z, y: +h.point.y.toFixed(2), geo: o.geometry.type,
      size: p.width ? `${p.width?.toFixed(1)}×${p.height?.toFixed(1)}` : (p.radius ? 'r' + p.radius : ''),
      color: c, chain: chain.slice(0, 4).join('<'),
    });
  }
  return res;
}, pts);
for (const r of out) {
  console.log(`  (${String(r.x).padStart(5)},${String(r.z).padStart(5)})  ${r.hit ? r.hit : `${r.geo} ${r.size || ''} y=${r.y} ${r.color}  ${r.chain}`}`);
}
await browser.close();
