// 判定 office_monitor 模型自身朝向：孤立渲染，前后各拍一张
// COO 房 coo(cx15.4, cz15.9) 桌面显示器本地 (±) → 世界 (15.55, 14.78) / (16.45, 14.78)
import { chromium } from './node_modules/playwright/index.mjs';
import { rtShot } from './grab.mjs';
const BASE = 'http://127.0.0.1:8934/office-3d-taskboard.html';
const OUT = 'C:/Users/Perfect/Desktop/3d-taskboard-main/_shots/';
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe' });
const page = await browser.newPage({ viewport: { width: 900, height: 700 } });
await page.goto(BASE, { waitUntil: 'domcontentloaded' });
await page.waitForFunction(() => !!window.__boardDebug, { timeout: 20000 });
await page.waitForTimeout(16000);

const found = await page.evaluate(async () => {
  const THREE = await import('three');
  const d = window.__boardDebug;
  const target = new THREE.Vector3(3.52, 0.96, 19.05);
  let best = null;
  d.scene.traverse(o => {
    if (!o.isGroup) return;
    const bb = new THREE.Box3().setFromObject(o);
    if (!bb.containsPoint(target)) return;
    const s = bb.getSize(new THREE.Vector3());
    if (s.x > 0.6 || s.y > 0.6 || s.z > 0.6) return;
    const vol = s.x * s.y * s.z;
    if (!best || vol < best.vol) best = { o, vol, s: s.toArray(), c: bb.getCenter(new THREE.Vector3()).toArray(), rotY: o.rotation.y };
  });
  if (!best) {
    const near = [];
    d.scene.traverse(o => {
      if (!o.isGroup) return;
      const bb = new THREE.Box3().setFromObject(o);
      const s2 = bb.getSize(new THREE.Vector3());
      const c = bb.getCenter(new THREE.Vector3());
      if (Math.hypot(c.x - 15.25, c.z - 14.78) < 2.2 && s2.x < 3) near.push({ name: o.name || o.type, s: s2.toArray().map(v => +v.toFixed(2)), c: c.toArray().map(v => +v.toFixed(2)) });
    });
    return { err: 'not found', near: near.slice(0, 25) };
  }
  d.__pick = best.o;
  best.o.traverse(o => { if (o.isMesh) o.userData.__wasVisible = o.visible; });
  d.scene.traverse(o => { if (o.isMesh) o.visible = false; });
  best.o.traverse(o => { o.visible = true; });
  d.scene.background = null;
  return { size: best.s.map(v => +v.toFixed(3)), center: best.c.map(v => +v.toFixed(3)), rotY: +best.rotY.toFixed(4), name: best.o.name };
});
console.log('found', JSON.stringify(found));

async function shotAt(file, off) {
  await page.evaluate(([off]) => {
    const d = window.__boardDebug;
    const p = d.__pick;
    const w = new (d.camera.position.constructor)();
    p.getWorldPosition(w);
    d.camera.position.set(w.x + off[0], w.y + off[1], w.z + off[2]);
    d.controls.target.set(w.x, w.y, w.z);
    d.camera.lookAt(w.x, w.y, w.z);
    d.controls.update();
  }, [off]);
  await page.waitForTimeout(200);
  await rtShot(page, OUT + 'lap_' + file + '.png', 900, 700, 0x2b3038);
  console.log('  ✓', file);
}
await shotAt('m1_from_plusZ', [0, 0.10, 1.30]);
await shotAt('m2_from_minusZ', [0, 0.10, -1.30]);
await shotAt('m3_top', [0, 1.60, 0.01]);
await browser.close();
