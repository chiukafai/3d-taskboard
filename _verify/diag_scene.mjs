// 场景对象诊断：列出指定世界坐标区域内的网格（位置/尺寸/材质色）
import { chromium } from './node_modules/playwright/index.mjs';

const BASE = 'http://127.0.0.1:8934/office-3d-taskboard.html';
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe' });
const page = await browser.newPage({ viewport: { width: 900, height: 620 } });
await page.goto(BASE, { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(11000);

const out = await page.evaluate(() => {
  const d = window.__boardDebug;
  const inBox = (c, r) => c.x >= r[0] && c.x <= r[1] && c.z >= r[2] && c.z <= r[3];
  const dump = (label, r) => {
    const rows = [];
    d.scene.traverse(o => {
      if (!o.isMesh || !o.geometry) return;
      o.geometry.computeBoundingBox();
      const bb = o.geometry.boundingBox.clone().applyMatrix4(o.matrixWorld);
      const c = { x: (bb.min.x + bb.max.x) / 2, y: (bb.min.y + bb.max.y) / 2, z: (bb.min.z + bb.max.z) / 2 };
      if (!inBox(c, r)) return;
      const sx = bb.max.x - bb.min.x, sy = bb.max.y - bb.min.y, sz = bb.max.z - bb.min.z;
      const col = o.material && o.material.color ? '#' + o.material.color.getHexString() : '-';
      rows.push({ c: `(${c.x.toFixed(2)},${c.y.toFixed(2)},${c.z.toFixed(2)})`, s: `${sx.toFixed(2)}x${sy.toFixed(2)}x${sz.toFixed(2)}`, col, type: o.geometry.type });
    });
    return { label, n: rows.length, rows: rows.sort((a, b) => parseFloat(a.c.slice(1)) - parseFloat(b.c.slice(1))) };
  };
  // 1) CPO 左墙附近（门墙）
  const a = dump('CPO-左墙 x17.4~18.6, z6~12', [17.4, 18.6, 6, 12]);
  // 2) CPO 北墙（记忆屏应在 z≈5.16）
  const b = dump('CPO-北墙内侧 z4.9~5.5, x18~24', [18, 24, 4.9, 5.5]);
  // 3) CFO 北墙（门墙）
  const cx = dump('CFO-北墙 z12.6~13.4, x16~24', [16, 24, 12.6, 13.4]);
  // 4) 门 pivot 状态
  const doors = Object.entries(d.doorGroups).map(([k, p]) => {
    const wp = p.getWorldPosition(new p.position.constructor());
    return `${k}: pos(${wp.x.toFixed(2)},${wp.z.toFixed(2)}) rotY=${p.rotation.y.toFixed(2)} 子${p.children.length}`;
  });
  return { a, b, cx, doors };
});
console.log('=== ' + out.a.label + ' (' + out.a.n + ') ===');
out.a.rows.forEach(r => console.log('  ', r.c, r.s, r.col, r.type));
console.log('=== ' + out.b.label + ' (' + out.b.n + ') ===');
out.b.rows.forEach(r => console.log('  ', r.c, r.s, r.col, r.type));
console.log('=== ' + out.cx.label + ' (' + out.cx.n + ') ===');
out.cx.rows.forEach(r => console.log('  ', r.c, r.s, r.col, r.type));
console.log('=== doors ===');
out.doors.forEach(r => console.log('  ', r));
await browser.close();
