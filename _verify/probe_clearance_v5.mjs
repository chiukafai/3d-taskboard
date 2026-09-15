// v5 走廊净空实测：对公共区逐格从 y=1.6 垂直下打射线，看步行高度带(0.20~1.60m)内有没有实体
// 输出：① 主廊/西支廊逐断面净宽  ② 走廊内残留障碍物清单（v5 目标 = 0 件）
import { chromium } from './node_modules/playwright/index.mjs';
import fs from 'fs';

const PUBLIC = JSON.parse(fs.readFileSync('plan_v5.json', 'utf8')).public;
const BASE = 'http://127.0.0.1:8934/office-3d-taskboard.html';
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe' });
const page = await browser.newPage({ viewport: { width: 900, height: 700 } });
await page.goto(BASE, { waitUntil: 'domcontentloaded' });
await page.waitForFunction(() => !!window.__boardDebug, { timeout: 20000 });
await page.waitForTimeout(13000);

const res = await page.evaluate(async ({ PUBLIC }) => {
  const THREE = await import('three');
  const d = window.__boardDebug;
  const hidden = [];
  d.scene.traverse(o => {
    if (o.isMesh && o.geometry?.type === 'PlaneGeometry' && (o.geometry.parameters?.width || 0) >= 50) { o.visible = false; hidden.push(o); }
  });
  const rc = new THREE.Raycaster(); rc.far = 400;
  const G = 0.1;
  const inPub = (x, z) => PUBLIC.some(r => x >= r[0] - 1e-6 && x <= r[2] + 1e-6 && z >= r[1] - 1e-6 && z <= r[3] + 1e-6);
  const clear = (x, z) => {                         // 步行高度带内无实体？
    rc.set(new THREE.Vector3(x, 1.6, z), new THREE.Vector3(0, -1, 0));
    const h = rc.intersectObjects(d.scene.children, true).filter(o => o.object.isMesh && o.object.visible);
    return !(h.length && h[0].point.y > 0.20);
  };
  // ① 逐列扫主廊（z 8.2~12.4）
  const mainSect = [];
  for (let x = 7.4; x <= 29.35; x += 0.2) {
    let lo = null, hi = null;
    for (let z = 8.25; z <= 12.35; z += 0.1) if (inPub(x, z) && clear(x, z)) { if (lo === null) lo = z; hi = z; }
    if (lo !== null) mainSect.push({ x: +x.toFixed(1), lo: +lo.toFixed(1), hi: +hi.toFixed(1), w: +(hi - lo + 0.1).toFixed(1) });
  }
  // ② 西支廊逐行（x 7.4~11.4，z 12.4~21.6）
  const westSect = [];
  for (let z = 12.45; z <= 21.55; z += 0.2) {
    let lo = null, hi = null;
    for (let x = 7.45; x <= 11.35; x += 0.1) if (inPub(x, z) && clear(x, z)) { if (lo === null) lo = x; hi = x; }
    if (lo !== null) westSect.push({ z: +z.toFixed(1), lo: +lo.toFixed(1), hi: +hi.toFixed(1), w: +(hi - lo + 0.1).toFixed(1) });
  }
  // ③ 障碍物聚类（公共区内、步行带内挡路）
  const pts = [];
  for (let x = 0; x <= 29.6; x += 0.2) for (let z = 0; z <= 21.6; z += 0.2) {
    if (!inPub(x, z)) continue;
    if (!clear(x, z)) pts.push([+x.toFixed(1), +z.toFixed(1)]);
  }
  const cl = [];
  pts.forEach(p => {
    let hit = cl.find(c => Math.abs(c.cx - p[0]) < 1.4 && Math.abs(c.cz - p[1]) < 1.4);
    if (hit) { hit.n++; hit.cx = (hit.cx * (hit.n - 1) + p[0]) / hit.n; hit.cz = (hit.cz * (hit.n - 1) + p[1]) / hit.n; }
    else cl.push({ cx: p[0], cz: p[1], n: 1 });
  });
  hidden.forEach(o => o.visible = true);
  return { mainSect, westSect, clusters: cl.sort((a, b) => b.n - a.n) };
}, { PUBLIC });

const ws = res.mainSect.map(s => s.w);
console.log('① 东西主廊逐断面净宽（z 8.2~12.4，沿 x 每 0.2m 一处）');
console.log(`   断面数 ${ws.length}  最小 ${Math.min(...ws)}m  最大 ${Math.max(...ws)}m  ` +
  `众数 ${(() => { const m = {}; ws.forEach(v => m[v] = (m[v] || 0) + 1); return Object.entries(m).sort((a, b) => b[1] - a[1])[0][0]; })()}m`);
const narrow = res.mainSect.filter(s => s.w < 4.2);
console.log(narrow.length ? '   ⚠️ <4.2m 的断面：' + narrow.map(s => `x=${s.x}(${s.w}m)`).join(' ') : '   ✅ 全程 ≥4.2m，无收窄');

const ww = res.westSect.map(s => s.w);
console.log('\n② 西支廊逐断面净宽（x 7.4~11.4，沿 z 每 0.2m 一处）');
console.log(`   断面数 ${ww.length}  最小 ${Math.min(...ww)}m  最大 ${Math.max(...ww)}m`);
const seg1 = res.westSect.filter(s => s.z >= 12.6 && s.z <= 16.2), seg2 = res.westSect.filter(s => s.z >= 16.6);
console.log(`   上段(z 12.6~16.2 邻会议室) 最小净宽 ${Math.min(...seg1.map(s => s.w))}m`);
console.log(`   下段(z 16.6~21.6 邻 CFO)  最小净宽 ${Math.min(...seg2.map(s => s.w))}m`);
const anom = res.westSect.filter(s => s.w < 4.0);
if (anom.length) console.log('   · 西支廊下段（设计值 2.8m）：' + anom.map(s => `z=${s.z}→${s.w}m[x ${s.lo}~${s.hi}]`).join('  '));

console.log('\n③ 公共区步行带内障碍物聚类（v5 目标 = 0 件）');
if (!res.clusters.length) console.log('   ✅ 0 件 —— 走廊/圆厅已彻底净空');
else res.clusters.forEach(c => console.log(`   · (${c.cx.toFixed(1)}, ${c.cz.toFixed(1)}) 约 ${(c.n * 0.04).toFixed(1)} ㎡`));

await browser.close();
