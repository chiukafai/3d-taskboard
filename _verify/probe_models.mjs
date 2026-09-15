// 实测 all-models.js 里每类模型的原始包围盒尺寸 + 靠背朝向
// 用途：静态审计 furniture AABB 需要真实尺寸；座向检查需要真实朝向约定
import { chromium } from './node_modules/playwright/index.mjs';
const BASE = 'http://127.0.0.1:8934/office-3d-taskboard.html';
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe' });
const page = await browser.newPage({ viewport: { width: 800, height: 600 } });
await page.goto(BASE, { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(9000);

const out = await page.evaluate(async () => {
  const THREE = await import('three');
  const { GLTFLoader } = await import('three/addons/loaders/GLTFLoader.js');
  const { DRACOLoader } = await import('three/addons/loaders/DRACOLoader.js');
  const draco = new DRACOLoader();
  draco.setDecoderPath('https://cdn.jsdelivr.net/npm/three@0.157.0/examples/jsm/libs/draco/');
  const loader = new GLTFLoader(); loader.setDRACOLoader(draco);
  const res = {};
  for (const k of Object.keys(window.OFFICE_MODELS)) {
    try {
      const bin = Uint8Array.from(atob(window.OFFICE_MODELS[k]), c => c.charCodeAt(0));
      const gltf = await new Promise((ok, no) => loader.parse(bin.buffer, '', ok, no));
      const box = new THREE.Box3().setFromObject(gltf.scene);
      const s = new THREE.Vector3(); box.getSize(s);
      // 上部（> 62% 高）顶点的 z 质心：判断靠背朝向（负=靠背在 -Z）
      let sum = 0, n = 0;
      gltf.scene.traverse(o => {
        if (!o.isMesh || !o.geometry?.attributes?.position) return;
        const p = o.geometry.attributes.position;
        for (let i = 0; i < p.count; i++) {
          const y = p.getY(i);
          if (y > box.min.y + s.y * 0.62) { sum += p.getZ(i); n++; }
        }
      });
      res[k] = { sx: +s.x.toFixed(3), sy: +s.y.toFixed(3), sz: +s.z.toFixed(3),
                 zcx: +(sum / Math.max(n, 1)).toFixed(3), n };
    } catch (e) { res[k] = { err: String(e).slice(0, 60) }; }
  }
  return res;
});
console.log('=== 模型原始尺寸（h 缩放前的自身坐标系）===');
for (const [k, v] of Object.entries(out)) {
  if (v.err) { console.log(`  ${k.padEnd(16)} ERROR ${v.err}`); continue; }
  const back = Math.abs(v.zcx) < 0.03 ? '双向对称' : (v.zcx < 0 ? '靠背/重体在 −Z' : '靠背/重体在 +Z');
  console.log(`  ${k.padEnd(16)} ${String(v.sx).padStart(6)} × ${String(v.sy).padStart(6)} × ${String(v.sz).padStart(6)}   上部z质心 ${String(v.zcx).padStart(7)}  ${back}`);
}
await browser.close();
