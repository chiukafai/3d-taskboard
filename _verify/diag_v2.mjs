// 重排后几何复核：① CPO 门洞通道内是否有遮挡物 ② 白板是否已移到 CMO 东墙
//                ③ CFO 门牌是否在 CFO 房内 + 朝向 ④ z=5 墙带上的实体分段
import { chromium } from './node_modules/playwright/index.mjs';

const BASE = 'http://127.0.0.1:8934/office-3d-taskboard.html';
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe' });
const page = await browser.newPage({ viewport: { width: 900, height: 620 } });
await page.goto(BASE, { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(12000);

const out = await page.evaluate(() => {
  const d = window.__boardDebug;
  const THREE_Vec3 = d.camera.position.constructor;

  // 收集所有 mesh 的 world bbox
  const meshes = [];
  d.scene.traverse(o => {
    if (!o.isMesh || !o.geometry) return;
    o.geometry.computeBoundingBox();
    const bb = o.geometry.boundingBox.clone().applyMatrix4(o.matrixWorld);
    const nx = o.material && o.material.name ? o.material.name : '';
    meshes.push({
      min: [bb.min.x, bb.min.y, bb.min.z], max: [bb.max.x, bb.max.y, bb.max.z],
      name: o.name || nx || '', visible: o.visible,
      col: o.material && o.material.color ? '#' + o.material.color.getHexString() : '-',
    });
  });

  // 门洞通道盒：世界坐标 (x0,x1,y0,y1,z0,z1) 内、且「有体积」的实体
  const inCorridor = (c) => meshes.filter(m =>
    m.visible && m.name !== '' || true
  ).filter(m => {
    const cx = (m.min[0] + m.max[0]) / 2, cy = (m.min[1] + m.max[1]) / 2, cz = (m.min[2] + m.max[2]) / 2;
    const sx = m.max[0] - m.min[0], sy = m.max[1] - m.min[1], sz = m.max[2] - m.min[2];
    // 中心在通道内 且 xz 尺寸 > 0.05（排除地面/大平板）
    return cx >= c[0] && cx <= c[1] && cy >= c[2] && cy <= c[3] && cz >= c[4] && cz <= c[5]
      && sx <= 3 && sz <= 3 && sy > 0.08;
  }).map(m => ({
    n: m.name, col: m.col,
    c: `(${((m.min[0] + m.max[0]) / 2).toFixed(2)},${((m.min[1] + m.max[1]) / 2).toFixed(2)},${((m.min[2] + m.max[2]) / 2).toFixed(2)})`,
    s: `${(m.max[0] - m.min[0]).toFixed(2)}x${(m.max[1] - m.min[1]).toFixed(2)}x${(m.max[2] - m.min[2]).toFixed(2)}`,
  }));

  // ①~③ 三处原问题区域
  const cpoDoorHall = inCorridor([20.6, 21.4, 0.15, 2.4, 5.0, 6.3]);   // CPO 门外通道
  const cfoDoorHall = inCorridor([19.6, 20.4, 0.15, 2.4, 11.8, 13.2]); // CFO 门外通道
  const cmoEastWall = meshes.filter(m => {
    const cx = (m.min[0] + m.max[0]) / 2, cz = (m.min[2] + m.max[2]) / 2;
    return cx > 22.5 && cz > 5.5 && cz < 12.5 && (m.min[1] < 2.5);
  }).map(m => ({
    c: `(${((m.min[0] + m.max[0]) / 2).toFixed(2)},${((m.min[1] + m.max[1]) / 2).toFixed(2)},${((m.min[2] + m.max[2]) / 2).toFixed(2)})`,
    s: `${(m.max[0] - m.min[0]).toFixed(2)}x${(m.max[1] - m.min[1]).toFixed(2)}x${(m.max[2] - m.min[2]).toFixed(2)}`,
    col: m.col, n: m.name,
  }));

  // ④ z=5 墙带（CPO 门段 x18~24）实体分段
  const wallAtZ5 = meshes.filter(m => {
    const cz = (m.min[2] + m.max[2]) / 2;
    const cx = (m.min[0] + m.max[0]) / 2;
    const sy = m.max[1] - m.min[1];
    return Math.abs(cz - 5) < 0.25 && cx > 17.5 && cx < 24.5 && sy > 0.5;
  }).map(m => ({
    x: `${(m.min[0]).toFixed(2)}~${(m.max[0]).toFixed(2)}`,
    y: `${(m.min[1]).toFixed(2)}~${(m.max[1]).toFixed(2)}`,
    z: `${(m.min[2]).toFixed(2)}~${(m.max[2]).toFixed(2)}`,
  }));

  // 门牌（canvas 贴图平面）定位
  const plaques = [];
  d.scene.traverse(o => {
    if (!o.isMesh || !o.geometry) return;
    const m = o.material;
    if (m && m.map && m.map.image && m.map.image.width && !m.map.image.height) { /* noop */ }
    if (m && m.map && m.map.image && m.map.image.tagName === 'CANVAS') {
      o.geometry.computeBoundingBox();
      const bb = o.geometry.boundingBox.clone().applyMatrix4(o.matrixWorld);
      const cx = (bb.min.x + bb.max.x) / 2, cy = (bb.min.y + bb.max.y) / 2, cz = (bb.min.z + bb.max.z) / 2;
      plaques.push({
        c: `(${cx.toFixed(2)},${cy.toFixed(2)},${cz.toFixed(2)})`,
        s: `${(bb.max.x - bb.min.x).toFixed(2)}x${(bb.max.y - bb.min.y).toFixed(2)}x${(bb.max.z - bb.min.z).toFixed(2)}`,
        rotY: (() => { const q = new (o.quaternion.constructor)(); o.getWorldQuaternion(q); return q; })(),
        e: [o.matrixWorld.elements[0], o.matrixWorld.elements[2]],
      });
    }
  });

  return { cpoDoorHall, cfoDoorHall, cmoEastWall, wallAtZ5, plaques };
});

console.log('① CPO 门外通道内实体 (' + out.cpoDoorHall.length + ')');
out.cpoDoorHall.forEach(r => console.log('   ', r.c, r.s, r.col, r.n));
console.log('② CFO 门外通道内实体 (' + out.cfoDoorHall.length + ')');
out.cfoDoorHall.forEach(r => console.log('   ', r.c, r.s, r.col, r.n));
console.log('③ CMO 东墙区 (x>22.5, z5.5~12.5) 实体 (' + out.cmoEastWall.length + ')');
out.cmoEastWall.forEach(r => console.log('   ', r.c, r.s, r.col, r.n));
console.log('④ z≈5 墙带 x17.5~24.5 实体分段 (' + out.wallAtZ5.length + ')');
out.wallAtZ5.forEach(r => console.log('   x', r.x, ' y', r.y, ' z', r.z));
console.log('⑤ 门牌类物体 (' + out.plaques.length + ')');
out.plaques.forEach(r => console.log('   ', r.c, r.s, 'horiz=[', r.e.map(v => v.toFixed(2)).join(','), ']'));

await browser.close();
