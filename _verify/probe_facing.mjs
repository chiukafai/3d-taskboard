// 实测 GLB 家具模型自身朝向：解析 exec_chair / exec_desk / office_chair，
// 打印各子网格相对包围盒中心的偏移，用以判断「靠背」在 +z 还是 -z。
import { chromium } from './node_modules/playwright/index.mjs';

const BASE = 'http://127.0.0.1:8934/office-3d-taskboard.html';
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe' });
const page = await browser.newPage({ viewport: { width: 800, height: 600 } });
await page.goto(BASE, { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(11000);

const out = await page.evaluate(async () => {
  const THREE = await import('three');
  const { GLTFLoader } = await import('three/addons/loaders/GLTFLoader.js');
  const { DRACOLoader } = await import('three/addons/loaders/DRACOLoader.js');
  const loader = new GLTFLoader();
  const draco = new DRACOLoader();
  draco.setDecoderPath('https://cdn.jsdelivr.net/npm/three@0.157.0/examples/jsm/libs/draco/');
  loader.setDRACOLoader(draco);
  const load = (k) => new Promise((res, rej) => {
    const bin = Uint8Array.from(atob(window.OFFICE_MODELS[k]), c => c.charCodeAt(0));
    loader.parse(bin.buffer, '', g => res(g), rej);
  });
  const report = {};
  for (const key of ['exec_chair', 'exec_desk', 'office_chair']) {
    if (!window.OFFICE_MODELS[key]) { report[key] = 'MISSING'; continue; }
    const g = await load(key);
    const root = g.scene;
    root.updateMatrixWorld(true);
    const full = new THREE.Box3().setFromObject(root);
    const fc = new THREE.Vector3(); full.getCenter(fc);
    const rows = [];
    root.traverse(o => {
      if (!o.isMesh || !o.geometry) return;
      o.geometry.computeBoundingBox();
      const bb = o.geometry.boundingBox.clone().applyMatrix4(o.matrixWorld);
      const c = new THREE.Vector3(); bb.getCenter(c);
      const s = new THREE.Vector3(); bb.getSize(s);
      rows.push({
        dz: +(c.z - fc.z).toFixed(3), dy: +(c.y - fc.y).toFixed(3), dx: +(c.x - fc.x).toFixed(3),
        sz: +s.z.toFixed(3), sy: +s.y.toFixed(3), sx: +s.x.toFixed(3),
        top: +bb.max.y.toFixed(3),
      });
    });
    rows.sort((a, b) => b.top - a.top);
    report[key] = { size: [+(full.max.x - full.min.x).toFixed(2), +(full.max.y - full.min.y).toFixed(2), +(full.max.z - full.min.z).toFixed(2)], rows: rows.slice(0, 12) };
  }
  return report;
});

for (const [k, v] of Object.entries(out)) {
  console.log(`\n=== ${k} ===`);
  if (v === 'MISSING') { console.log('  缺失'); continue; }
  console.log('  整体尺寸 xyz =', v.size.join(' x '));
  console.log('  子网格（按高度降序）: dx, dy, dz = 相对中心偏移; s* = 尺寸');
  v.rows.forEach(r => console.log(`    dy=${String(r.dy).padStart(7)} dz=${String(r.dz).padStart(7)} dx=${String(r.dx).padStart(7)}  s=${r.sx}x${r.sy}x${r.sz}`));
}
await browser.close();
