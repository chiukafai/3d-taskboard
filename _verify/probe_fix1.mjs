// 诊断：① 门牌朝向（正面/背面哪一面对着走廊） ② CFO 地毯重叠 ③ 桌面模型尺寸
import { chromium } from './node_modules/playwright/index.mjs';
const BASE = 'http://127.0.0.1:8934/office-3d-taskboard.html';
const OUT = 'C:/Users/Perfect/Desktop/3d-taskboard-main/_shots/';
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe' });
const page = await browser.newPage({ viewport: { width: 1400, height: 1000 } });
await page.goto(BASE, { waitUntil: 'domcontentloaded' });
await page.waitForFunction(() => !!window.__boardDebug, { timeout: 20000 });
await page.waitForTimeout(15000);

const diag = await page.evaluate(async () => {
  const THREE = await import('three');
  const d = window.__boardDebug;
  const out = { plaques: [], rugs: [], desk: [] };

  // ── ① 门牌：找 5 个子节点(kind=bg/frame/frameR/front/back)的 Group ──
  const rooms = d.scene.children.filter(o => o.isGroup && o.children.some(c => c.userData && c.userData.__zone));
  const zoneGroups = d.scene.children.filter(o => o.isGroup && o.children.length >= 5);
  for (const rg of zoneGroups) {
    const inner = rg.children.find(c => c.isGroup && c.children.length >= 5 && c.children.some(x => x.isMesh && x.geometry && x.geometry.type === 'BoxGeometry' && x.geometry.parameters.depth === 0.06));
    if (!inner) continue;
    const wp = new THREE.Vector3(), wq = new THREE.Quaternion(), ws = new THREE.Vector3();
    inner.updateWorldMatrix(true, false);
    inner.matrixWorld.decompose(wp, wq, ws);
    const nrm = new THREE.Vector3(0, 0, 1).applyQuaternion(wq);       // 正面法线
    const rp = rg.getWorldPosition(new THREE.Vector3());
    const outward = new THREE.Vector3(wp.x - rp.x, 0, wp.z - rp.z).normalize();
    const dot = nrm.x * outward.x + nrm.z * outward.z;
    out.plaques.push({
      room: rg.name || ('grp' + rg.id),
      plaqueAt: [+wp.x.toFixed(2), +wp.y.toFixed(2), +wp.z.toFixed(2)],
      roomAt: [+rp.x.toFixed(2), +rp.z.toFixed(2)],
      normal: [+nrm.x.toFixed(2), +nrm.z.toFixed(2)],
      dot: +dot.toFixed(3),
      verdict: dot > 0.3 ? '正面朝外 ✓' : (dot < -0.3 ? '背面朝外 ✗(镜字)' : '侧向'),
    });
  }

  // ── ② 地毯：找所有 y≈0.095 的 PlaneGeometry ──
  d.scene.traverse(o => {
    if (o.isMesh && o.geometry && o.geometry.type === 'PlaneGeometry') {
      o.updateWorldMatrix(true, false);
      const bb = new THREE.Box3().setFromObject(o);
      if (bb.min.y > 0.05 && bb.min.y < 0.14) {
        out.rugs.push({
          size: [+(bb.max.x - bb.min.x).toFixed(2), +(bb.max.z - bb.min.z).toFixed(2)],
          y: +bb.min.y.toFixed(3),
          x: [+bb.min.x.toFixed(2), +bb.max.x.toFixed(2)],
          z: [+bb.min.z.toFixed(2), +bb.max.z.toFixed(2)],
        });
      }
    }
  });
  // 重叠检测
  const R = out.rugs;
  out.rugOverlap = [];
  for (let i = 0; i < R.length; i++) for (let j = i + 1; j < R.length; j++) {
    const ox = Math.min(R[i].x[1], R[j].x[1]) - Math.max(R[i].x[0], R[j].x[0]);
    const oz = Math.min(R[i].z[1], R[j].z[1]) - Math.max(R[i].z[0], R[j].z[0]);
    if (ox > 0.01 && oz > 0.01 && Math.abs(R[i].y - R[j].y) < 0.02)
      out.rugOverlap.push({ i, j, ox: +ox.toFixed(2), oz: +oz.toFixed(2) });
  }

  // ── ③ 桌面模型：CRO 房里 office_monitor / exec_desk 的世界包围盒 ──
  const croGrp = d.scene.children.find(o => o.isGroup && o.children.length >= 5 && o.position.x > 12 && o.position.x < 13 && o.position.z > 5 && o.position.z < 7);
  const keyOf = o => (o.userData && o.userData.__key) || '';
  if (croGrp) {
    croGrp.traverse(o => {
      if (o.isMesh) {
        const bb = new THREE.Box3().setFromObject(o);
        const s = bb.getSize(new THREE.Vector3());
        if (s.y > 0.3 && s.y < 1.3 && bb.min.y < 1.2) out.desk.push({ key: keyOf(o), size: [+s.x.toFixed(2), +s.y.toFixed(2), +s.z.toFixed(2)], min: [+bb.min.x.toFixed(2), +bb.min.y.toFixed(2), +bb.min.z.toFixed(2)] });
      }
    });
  }
  return out;
});
console.log(JSON.stringify(diag, null, 1).slice(0, 6000));

// ── 截图 ──
const shots = [
  ['z1_cfo_plaque', 11.6, 1.75, 19.0, 8.74, 2.35, 19.0],
  ['z2_cpo_plaque', 9.6, 1.75, 9.6, 6.74, 2.35, 9.6],
  ['z3_cfo_rugs_top', 5.4, 11.0, 19.0, 5.4, 0.0, 19.0],
  ['z4_cro_desk', 12.9, 2.30, 6.10, 12.5, 0.80, 4.40],
  ['z5_ceo_desk', 22.7, 2.30, 16.90, 21.8, 0.80, 14.55],
];
for (const [n, px, py, pz, lx, ly, lz] of shots) {
  await page.evaluate(([px, py, pz, lx, ly, lz]) => {
    const d = window.__boardDebug;
    d.scene.fog = null;
    d.camera.position.set(px, py, pz);
    d.controls.target.set(lx, ly, lz);
    d.camera.lookAt(lx, ly, lz);
    d.controls.update();
  }, [px, py, pz, lx, ly, lz]);
  await page.waitForTimeout(1200);
  await page.screenshot({ path: OUT + n + '.png' });
  console.log('  ✓', n);
}
await browser.close();
