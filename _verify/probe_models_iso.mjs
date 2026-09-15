// 模型单件隔离渲染：把 9 个 GLB 各摆一份到干净地面，3/4 视角出图 → 看清每个模型自身内容
// 用途：判断"桌上两台笔记本/圆盘托底"到底是模型自带，还是代码重复摆放
import { chromium } from './node_modules/playwright/index.mjs';
import { rtShot, look } from './grab.mjs';

const BASE = 'http://127.0.0.1:8934/office-3d-taskboard.html';
const OUT = 'C:/Users/Perfect/Desktop/3d-taskboard-main/_shots/iso_models.png';

const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe' });
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
await page.goto(BASE, { waitUntil: 'domcontentloaded' });
await page.waitForFunction(() => !!window.__boardDebug, { timeout: 20000 });
await page.waitForTimeout(17000);   // 等模型包 + 8 房就位

const info = await page.evaluate(async () => {
  const THREE = await import('three');
  const { GLTFLoader } = await import('three/addons/loaders/GLTFLoader.js');
  const { DRACOLoader } = await import('three/addons/loaders/DRACOLoader.js');
  const d = window.__boardDebug;

  // 1) 隐藏原场景（保留灯光），铺一块干净地面
  const restore = [];
  d.scene.children.forEach(o => {
    if (o.isLight || o === d.camera) return;
    restore.push([o, o.visible]); o.visible = false;
  });
  const lib = new THREE.Group(); lib.name = 'isoLib';
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(40, 20),
    new THREE.MeshStandardMaterial({ color: 0xcfc9bd, roughness: 0.95 }));
  floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true; lib.add(floor);
  d.scene.add(lib);

  // 2) 解析 9 个模型
  const loader = new GLTFLoader();
  const draco = new DRACOLoader();
  draco.setDecoderPath('https://cdn.jsdelivr.net/npm/three@0.157.0/examples/jsm/libs/draco/');
  loader.setDRACOLoader(draco);
  const keys = Object.keys(window.OFFICE_MODELS);
  const out = [];
  const parse = k => new Promise((res, rej) => {
    const bin = Uint8Array.from(atob(window.OFFICE_MODELS[k]), c => c.charCodeAt(0));
    loader.parse(bin.buffer, '', res, rej);
  });

  const cols = 5, gap = 2.4;
  for (let i = 0; i < keys.length; i++) {
    const k = keys[i];
    const gltf = await parse(k);
    const root = gltf.scene;
    // 原生包围盒（含节点旋转）
    const bb0 = new THREE.Box3().setFromObject(root);
    const s0 = bb0.getSize(new THREE.Vector3());
    const holder = new THREE.Group();
    holder.add(root);
    holder.position.set((i % cols - 2) * gap, 0, Math.floor(i / cols) * gap * 0.9);
    root.position.y -= bb0.min.y;      // 落地
    lib.add(holder);
    const bb1 = new THREE.Box3().setFromObject(holder);
    const s1 = bb1.getSize(new THREE.Vector3());
    out.push({ key: k, native: [+s0.x.toFixed(3), +s0.y.toFixed(3), +s0.z.toFixed(3)],
               world: [+s1.x.toFixed(3), +s1.y.toFixed(3), +s1.z.toFixed(3)] });
    // 每个模型单独记录其网格数，判断是否"一体成型"
    let meshes = 0; root.traverse(o => { if (o.isMesh) meshes++; });
    out[out.length - 1].meshes = meshes;
  }
  window.__isoRestore = restore;
  return out;
});

console.log('原生包围盒（未缩放，含节点旋转）:');
for (const r of info) {
  console.log(`  ${r.key.padEnd(16)} 原生 ${String(r.native).padEnd(24)} 摆位后 ${String(r.world).padEnd(24)} mesh=${r.meshes}`);
}
const json = JSON.stringify(info, null, 1);
const fs = await import('node:fs');
fs.writeFileSync('C:/Users/Perfect/Desktop/3d-taskboard-main/_verify/_models_iso.json', json);

await look(page, 0, 4.6, 7.6, 0, 0.5, 1.2);
await rtShot(page, OUT);
console.log('出图 →', OUT);
await browser.close();
