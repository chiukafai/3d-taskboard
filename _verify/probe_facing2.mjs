// 通过顶点分布判断模型朝向：
// 椅子 → 取最高的 25% 顶点（靠背），看其相对整体中心的 z/x 偏移；
//        靠背在 -z ⇒ 面朝 +z（r=0），靠背在 +z ⇒ 面朝 -z。
// 桌子 → 取最低 35% 顶点（桌腿/柜体）与最高顶点（桌面）分布，判断「使用者一侧」。
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

  const analyze = (root) => {
    root.updateMatrixWorld(true);
    const full = new THREE.Box3().setFromObject(root);
    const fc = new THREE.Vector3(); full.getCenter(fc);
    const H = full.max.y - full.min.y;
    const pts = [];
    root.traverse(o => {
      if (!o.isMesh || !o.geometry) return;
      const pos = o.geometry.attributes.position;
      const v = new THREE.Vector3();
      for (let i = 0; i < pos.count; i++) {
        v.fromBufferAttribute(pos, i).applyMatrix4(o.matrixWorld);
        pts.push([v.x, v.y, v.z]);
      }
    });
    const band = (y0, y1) => {
      const s = pts.filter(p => p[1] >= full.min.y + H * y0 && p[1] <= full.min.y + H * y1);
      if (!s.length) return null;
      const m = k => s.reduce((a, p) => a + p[k], 0) / s.length;
      return { n: s.length, mx: +(m(0) - fc.x).toFixed(3), my: +(m(1) - fc.y).toFixed(3), mz: +(m(2) - fc.z).toFixed(3) };
    };
    return {
      n: pts.length,
      size: [+(full.max.x - full.min.x).toFixed(2), +H.toFixed(2), +(full.max.z - full.min.z).toFixed(2)],
      top25: band(0.75, 1.0), top10: band(0.9, 1.0),
      mid: band(0.4, 0.6), low35: band(0.0, 0.35), low10: band(0.0, 0.1),
    };
  };

  const res = {};
  for (const k of ['exec_chair', 'office_chair', 'exec_desk', 'filing_cabinet', 'sofa', 'office_monitor', 'laptop', 'coffee_table']) {
    if (!window.OFFICE_MODELS[k]) { res[k] = 'MISSING'; continue; }
    res[k] = analyze((await load(k)).scene);
  }
  return res;
});

for (const [k, v] of Object.entries(out)) {
  console.log(`\n=== ${k} ===`);
  if (v === 'MISSING') { console.log('  缺失'); continue; }
  console.log(`  顶点数=${v.n}  尺寸 xyz = ${v.size.join(' x ')}`);
  for (const b of ['top10', 'top25', 'mid', 'low35', 'low10']) {
    if (v[b]) console.log(`  ${b.padEnd(6)} n=${String(v[b].n).padStart(6)}  dx=${String(v[b].mx).padStart(7)} dy=${String(v[b].my).padStart(7)} dz=${String(v[b].mz).padStart(7)}`);
  }
}
await browser.close();
