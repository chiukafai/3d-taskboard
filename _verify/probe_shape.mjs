// 打印模型俯视/侧视 ASCII 占据图（可直接阅读，绕过无法看图的问题）
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

  const grid = (root, axis, N) => {
    root.updateMatrixWorld(true);
    const box = new THREE.Box3().setFromObject(root);
    const c = new THREE.Vector3(); box.getCenter(c);
    const size = new THREE.Vector3(); box.getSize(size);
    const pts = [];
    root.traverse(o => {
      if (!o.isMesh || !o.geometry) return;
      const pos = o.geometry.attributes.position; const v = new THREE.Vector3();
      for (let i = 0; i < pos.count; i++) { v.fromBufferAttribute(pos, i).applyMatrix4(o.matrixWorld); pts.push([v.x, v.y, v.z]); }
    });
    // axis='xz' 俯视(|y|加权) ; axis='xy' 正视 z 向 ; axis='zy' 侧视 x 向
    const pick = axis === 'xz' ? [0, 1, 2] : axis === 'xy' ? [0, 2, 1] : [2, 0, 1];
    const a0 = pick[0], a1 = pick[1], depth = pick[2];
    const lo0 = Math.min(...pts.map(p => p[a0])), hi0 = Math.max(...pts.map(p => p[a0]));
    const lo1 = Math.min(...pts.map(p => p[a1])), hi1 = Math.max(...pts.map(p => p[a1]));
    const loD = Math.min(...pts.map(p => p[depth])), hiD = Math.max(...pts.map(p => p[depth]));
    const g = Array.from({ length: N }, () => new Array(N).fill(0));
    pts.forEach(p => {
      const i = Math.min(N - 1, Math.max(0, Math.floor((p[a0] - lo0) / (hi0 - lo0 || 1) * N)));
      // 行序：从上往下 = 轴1 从大到小，便于像平面图一样阅读
      const j = Math.min(N - 1, Math.max(0, Math.floor((p[a1] - lo1) / (hi1 - lo1 || 1) * N)));
      const w = (p[depth] - loD) / (hiD - loD || 1) * 3 + 0.4;
      g[N - 1 - j][i] += w;
    });
    const mx = Math.max(...g.flat());
    const ramp = ' .:-=+*#%@';
    return {
      size: [+size.x.toFixed(2), +size.y.toFixed(2), +size.z.toFixed(2)],
      lo0: +lo0.toFixed(2), hi0: +hi0.toFixed(2), lo1: +lo1.toFixed(2), hi1: +hi1.toFixed(2),
      art: g.map(r => r.map(v => ramp[Math.min(9, Math.floor(v / mx * 9.99))]).join('')).join('\n'),
    };
  };

  const res = {};
  for (const k of ['exec_desk', 'exec_chair']) {
    const g = await load(k);
    res[k] = { xz: grid(g.scene, 'xz', 34), xy: grid(g.scene, 'xy', 34) };
    // 注意：克隆后再测，避免 matrixWorld 已被前面调用改动
    const g2 = await load(k);
    res[k].zy = grid(g2.scene, 'zy', 34);
  }
  return res;
});

for (const [k, v] of Object.entries(out)) {
  console.log(`\n########## ${k}  尺寸 xyz=${v.size ? '' : ''}${v.xz.size.join(' x ')}`);
  console.log(`--- 俯视图 (x 向右 →, z 向下 ↑ 表示 -z 在上方? 实际 lo1..hi1 = ${v.xz.lo1}..${v.xz.hi1}) ---`);
  console.log('     x: ' + v.xz.lo0 + ' → ' + v.xz.hi0 + '   (上=z' + v.xz.hi1 + ', 下=z' + v.xz.lo0 === '' ? '' : v.xz.hi1 + ')');
  console.log(v.xz.art);
  console.log(`--- 正视图 (x 向右, y 向上) ---`);
  console.log(v.xy.art);
  console.log(`--- 侧视图 (z 向右, y 向上) ---`);
  console.log(v.zy.art);
}
await browser.close();
