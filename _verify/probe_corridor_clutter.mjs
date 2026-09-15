// 枚举"当前落在走廊/圆厅内地面上"的实体 —— 用于生成准确的过道清障清单
// 做法：逐个 scene 根节点 → 展开一层子节点 → 世界包围盒 → 落在公共区且底 y<2 → 记为一件
import { chromium } from './node_modules/playwright/index.mjs';
const BASE = 'http://127.0.0.1:8934/office-3d-taskboard.html';
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe' });
const page = await browser.newPage({ viewport: { width: 1000, height: 700 } });
await page.goto(BASE, { waitUntil: 'domcontentloaded' });
await page.waitForFunction(() => !!window.__boardDebug, { timeout: 20000 });
await page.waitForTimeout(14000);

const out = await page.evaluate(async () => {
  const THREE = await import('three');
  const d = window.__boardDebug;
  const rects = JSON.parse('[[7.4,8.6,29.4,11.6],[8.6,11.6,10.2,21.6],[6.6,5.6,9.4,8.6],[19.4,11.6,29.4,12.4],[10.2,16.4,11.4,21.6],[7.4,11.6,8.6,16.4],[6.6,8.6,7.4,11.0],[10.2,11.6,11.4,13.0]]');
  const LB = { x: 9.4, z: 10.8, r: 1.9 };
  const inPub = (x, z) => {
    for (const r of rects) if (x >= r[0] && x <= r[2] && z >= r[1] && z <= r[3]) return true;
    return Math.hypot(x - LB.x, z - LB.z) <= LB.r;
  };
  const hits = [];
  const seen = new Set();
  d.scene.children.forEach(root => {
    const kids = (root.isGroup && root.children.length) ? root.children : [root];
    kids.forEach(node => {
      if (!node.isObject3D) return;
      const b = new THREE.Box3().setFromObject(node);
      if (!isFinite(b.min.x)) return;
      const s = b.getSize(new THREE.Vector3());
      const c = b.getCenter(new THREE.Vector3());
      if (s.x > 12 || s.z > 12) return;        // 大地面 / 大垫层 / 整组
      if (s.y < 0.05) return;                  // 纯地板
      if (b.min.y < -0.4) return;              // 垫层
      if (b.min.y > 1.85) return;              // 挂墙屏 / 吊顶
      if (!inPub(c.x, c.z)) return;
      const k = c.x.toFixed(1) + ',' + c.z.toFixed(1) + ',' + s.x.toFixed(1) + ',' + s.z.toFixed(1);
      if (seen.has(k)) return; seen.add(k);
      hits.push({ x: +c.x.toFixed(2), y: +b.min.y.toFixed(2), z: +c.z.toFixed(2),
                  w: +s.x.toFixed(2), h: +s.y.toFixed(2), dp: +s.z.toFixed(2) });
    });
  });
  return hits;
});

console.log('落在走廊 / 圆厅内的实体（地面物件）：');
out.sort((a, b) => a.x - b.x || a.z - b.z);
out.forEach(h => console.log(`  (x=${String(h.x).padStart(5)}, z=${String(h.z).padStart(5)})  底y=${h.y}  包围盒 ${h.w}W×${h.h}H×${h.dp}D`));
console.log('合计', out.length, '件');
await browser.close();
