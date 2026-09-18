/**
 * 墙体重合（z-fighting）检测 + 取证截图
 * 用法：node _verify/verify_wall_zfight.mjs [html文件] [输出标签]
 *   node _verify/verify_wall_zfight.mjs ../office-3d-taskboard.html.bak_pre_zfight_20260916 before
 *   node _verify/verify_wall_zfight.mjs ../office-3d-taskboard.html after
 * 判据：不同房间之间，两面「严格共面（<1mm）且互相重叠」的墙 → 深度值相等 → 必然闪烁。
 *      按共面面积分级：>1㎡ = 肉眼可见；<0.05㎡ = 可忽略。
 */
import { chromium } from './node_modules/playwright/index.mjs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const rel = process.argv[2] || '../office-3d-taskboard.html';
const tag = process.argv[3] || 'current';
const target = 'file:///' + path.resolve(here, rel).replace(/\\/g, '/');

const NAMES = {
  '3.3,8.3': 'CPO', '4.2,13.7': '会议室', '5.4,19': 'CFO', '12.5,5.9': 'CRO',
  '19.7,4.1': 'CMO', '26.7,4.9': 'CTO', '15.4,15.9': 'COO', '22.7,15.7': 'CEO',
};

const browser = await chromium.launch({
  headless: true,
  executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
});
const page = await browser.newPage({ viewport: { width: 1000, height: 640 }, deviceScaleFactor: 1.5 });
const errs = [];
page.on('pageerror', e => errs.push(String(e)));
await page.goto(target, { waitUntil: 'load' });
await page.waitForFunction(
  () => window.__boardDebug && window.__boardDebug.scene && window.__boardDebug.scene.children.length > 20,
  { timeout: 90000 });
await page.waitForTimeout(2500);

const res = await page.evaluate(() => {
  const sc = window.__boardDebug.scene;
  function aabb(m) {              // 不依赖全局 THREE：用 geometry.boundingBox + matrixWorld
    const g = m.geometry;
    if (!g.boundingBox) g.computeBoundingBox();
    const b = g.boundingBox; m.updateWorldMatrix(true, false);
    const e = m.matrixWorld.elements;
    const min = [Infinity, Infinity, Infinity], max = [-Infinity, -Infinity, -Infinity];
    [b.min.x, b.max.x].forEach(x => [b.min.y, b.max.y].forEach(y => [b.min.z, b.max.z].forEach(z => {
      const w = [e[0] * x + e[4] * y + e[8] * z + e[12],
                 e[1] * x + e[5] * y + e[9] * z + e[13],
                 e[2] * x + e[6] * y + e[10] * z + e[14]];
      for (let k = 0; k < 3; k++) { if (w[k] < min[k]) min[k] = w[k]; if (w[k] > max[k]) max[k] = w[k]; }
    })));
    return { min, max };
  }
  const ov = (A, B, a) => Math.min(A.max[a], B.max[a]) - Math.max(A.min[a], B.min[a]);

  const rooms = [];
  sc.children.forEach(o => {
    if (!o.isGroup) return;
    const walls = [];
    o.traverse(c => {
      if (c.isMesh && c.geometry && c.geometry.type === 'BoxGeometry' && c.geometry.parameters &&
          Math.abs(c.geometry.parameters.height - 2.8) < 1e-6) walls.push(c);
    });
    if (walls.length) rooms.push({ key: o.position.x.toFixed(1) + ',' + o.position.z.toFixed(1), walls });
  });

  const pairs = [];
  let minOverlapFace = 9;        // 体积重叠的两墙之间，X/Z 面上最小间距
  for (let i = 0; i < rooms.length; i++) for (let j = i + 1; j < rooms.length; j++) {
    rooms[i].walls.forEach(wa => rooms[j].walls.forEach(wb => {
      const A = aabb(wa), B = aabb(wb);
      if (![0, 1, 2].every(a => ov(A, B, a) > 1e-3)) return;      // 无体积重叠 → 不是问题
      let area = 0, axes = [];
      for (const a of [0, 2]) {                                   // 只看 X/Z（y 恒为 0~2.8，会误报）
        const others = [0, 1, 2].filter(x => x !== a);
        if (!others.every(x => ov(A, B, x) > 1e-3)) continue;
        const d = Math.min(Math.abs(A.min[a] - B.min[a]), Math.abs(A.max[a] - B.max[a]),
                           Math.abs(A.min[a] - B.max[a]), Math.abs(A.max[a] - B.min[a]));
        if (d < minOverlapFace) minOverlapFace = d;
        if (d < 1e-3) { area = Math.max(area, ov(A, B, others[0]) * ov(A, B, others[1])); axes.push('xz'[a === 0 ? 0 : 1]); }
      }
      if (area > 0) pairs.push({ a: rooms[i].key, b: rooms[j].key, axes: axes.join('+'), area: +area.toFixed(3),
        boxA: A.min.map(v => +v.toFixed(3)).join(',') + ' → ' + A.max.map(v => +v.toFixed(3)).join(','),
        boxB: B.min.map(v => +v.toFixed(3)).join(',') + ' → ' + B.max.map(v => +v.toFixed(3)).join(',') });
    }));
  }
  pairs.sort((p, q) => q.area - p.area);
  return {
    rooms: rooms.length, pairs,
    big: pairs.filter(p => p.area > 1).length,
    mid: pairs.filter(p => p.area > 0.05 && p.area <= 1).length,
    tiny: pairs.filter(p => p.area <= 0.05).length,
    minOverlapFace: +minOverlapFace.toFixed(4),
  };
});

// 取证截图：站进 CMO，正对与 CRO 的共墙（x=15.6 那道）
await page.evaluate(() => {
  const d = window.__boardDebug;
  d.controls.enableDamping = false; d.controls.enabled = false;
  d.camera.position.set(18.6, 1.55, 4.6);
  d.controls.target.set(15.6, 1.45, 4.6);
  d.camera.lookAt(15.6, 1.45, 4.6);
});
await page.waitForTimeout(900);
const shot = path.resolve(here, '../_shots/zfight_' + tag + '.png');
await page.screenshot({ path: shot });

console.log('== ' + tag + ' (' + path.basename(path.resolve(here, rel)) + ') ==');
console.log('房间组数            :', res.rooms);
console.log('共面重叠墙对        :', res.pairs.length, '（大面积>1㎡:', res.big, ' / 中:', res.mid, ' / 可忽略<0.05㎡:', res.tiny, '）');
res.pairs.forEach(p => { console.log('   ' + (p.area > 1 ? '✗' : '·'), (NAMES[p.a] || p.a), '↔', (NAMES[p.b] || p.b),
  '| 共面轴', p.axes, '| 共面面积', p.area, '㎡');
  console.log('       A[', p.boxA, ']');
  console.log('       B[', p.boxB, ']'); });
console.log('X/Z 面最小间距(m)   :', res.minOverlapFace);
console.log('页面报错            :', errs.length ? errs : '无');
console.log('截图                :', shot);
await browser.close();
