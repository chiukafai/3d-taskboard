// 检查大厅内部是否有残留隔墙（x≈18, z5~13）以及各房间正面墙分段
import { chromium } from './node_modules/playwright/index.mjs';
const BASE = 'http://127.0.0.1:8934/office-3d-taskboard.html';
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe' });
const page = await browser.newPage({ viewport: { width: 800, height: 600 } });
await page.goto(BASE, { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(11000);

const out = await page.evaluate(() => {
  const d = window.__boardDebug;
  const rows = [];
  d.scene.traverse(o => {
    if (!o.isMesh || !o.geometry) return;
    o.geometry.computeBoundingBox();
    const bb = o.geometry.boundingBox.clone().applyMatrix4(o.matrixWorld);
    const sy = bb.max.y - bb.min.y, sx = bb.max.x - bb.min.x, sz = bb.max.z - bb.min.z;
    if (sy < 1.5) return;                    // 只看高物（墙/隔断/柱）
    const cx = (bb.min.x + bb.max.x) / 2, cz = (bb.min.z + bb.max.z) / 2;
    // 落在大厅区域 z 5~13 内
    if (cz < 5 || cz > 13) return;
    if (cx < -1 || cx > 25) return;
    rows.push(`x ${bb.min.x.toFixed(2)}~${bb.max.x.toFixed(2)}  y ${bb.min.y.toFixed(2)}~${bb.max.y.toFixed(2)}  z ${bb.min.z.toFixed(2)}~${bb.max.z.toFixed(2)}`);
  });
  return rows;
});
console.log('=== 大厅区域 (z5~13, x-1~25) 内的高度>1.5m 实体 ===');
out.forEach(r => console.log('  ', r));
console.log('  合计', out.length, '件');
await browser.close();
